
import os
import re
import csv
import time
import hashlib
import xml.etree.ElementTree as ET

from pathlib import Path
from urllib.parse import urlparse
from difflib import SequenceMatcher

import requests
import pandas as pd
import fitz


# ============================================================
# CONFIGURATION
# ============================================================

MASTER = Path("pcs_merged_review.csv")

OLD_INVENTORY = Path(
    "results/pdf_acquisition_inventory_openalex.csv"
)

OLD_DISCOVERY = Path(
    "results/open_access_discovery_recovered.csv"
)

OLD_ATTEMPTS = Path(
    "results/openalex_pdf_download_attempts.csv"
)

OUTPUT = Path(
    "results/pdf_acquisition_all_196.csv"
)

LOG = Path(
    "results/pdf_acquisition_all_196_attempts.csv"
)

PDF_DIR = Path("papers/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

OPENALEX_API = "https://api.openalex.org/works"
ARXIV_API = "https://export.arxiv.org/api/query"

API_KEY = os.getenv("OPENALEX_API_KEY", "").strip()

MAX_BYTES = 100 * 1024 * 1024
TIMEOUT = 45
TITLE_THRESHOLD = 0.92

# Respect arXiv's request-spacing guidance.
ARXIV_DELAY = 3.0

# Existing unsuccessful URLs can be skipped to avoid
# repeatedly requesting blocked publisher endpoints.
SKIP_PREVIOUS_FAILURES = True

NS = {
    "atom": "http://www.w3.org/2005/Atom"
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize(text):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(text).casefold()
    ).strip()


def compact(text):
    return normalize(text).replace(" ", "")


def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


def valid_year(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def title_column(df):
    for column in df.columns:
        if column.strip().casefold() in (
            "title",
            "paper title"
        ):
            return column

    raise ValueError(
        "Cannot identify title column: "
        + str(list(df.columns))
    )


def make_filename(title):
    safe = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        str(title)
    ).strip("_")[:75]

    digest = hashlib.sha256(
        str(title).encode("utf-8")
    ).hexdigest()[:10]

    return f"{safe}_{digest}.pdf"


def paper_identifier(title):
    return hashlib.sha256(
        compact(title).encode("utf-8")
    ).hexdigest()[:16]


def is_media_url(url):
    path = urlparse(str(url)).path.lower()

    return path.endswith((
        ".mp4", ".mov", ".avi",
        ".mp3", ".zip", ".pptx",
        ".tar", ".gz"
    ))


def source_priority(url):
    domain = urlparse(url).netloc.lower()

    if domain.endswith("arxiv.org"):
        return 0

    if domain.endswith("eprint.iacr.org"):
        return 1

    if domain.endswith("hal.science"):
        return 2

    if domain.endswith("usenix.org"):
        return 3

    if (
        domain.endswith("dl.acm.org")
        or domain.endswith("ieeexplore.ieee.org")
    ):
        return 6

    return 4


def split_urls(value):
    return [
        url.strip()
        for url in str(value).split(" | ")
        if url.strip()
    ]


# ============================================================
# PDF VALIDATION
# ============================================================

def validate_pdf(path, title):
    try:
        with Path(path).open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                return False, "INVALID_PDF", 0

        with fitz.open(path) as doc:
            pages = doc.page_count

            if pages == 0:
                return False, "EMPTY_PDF", 0

            text = "\n".join(
                doc[i].get_text()
                for i in range(min(pages, 3))
            )

        if len(text.strip()) < 30:
            return False, "NO_EXTRACTABLE_TEXT", pages

        expected = normalize(title)
        extracted = normalize(text)

        if expected in extracted:
            return True, "TITLE_MATCH", pages

        target_words = expected.split()
        document_words = extracted.split()

        if not target_words:
            return True, "REVIEW_TITLE", pages

        width = len(target_words)
        best = 0.0

        # Compare similarly sized windows near
        # the start of the document.
        for start in range(min(
            len(document_words), 1200
        )):
            candidate = " ".join(
                document_words[start:start + width]
            )

            score = similarity(
                expected,
                candidate
            )

            best = max(best, score)

            if best >= TITLE_THRESHOLD:
                break

        if best >= TITLE_THRESHOLD:
            return True, "TITLE_MATCH", pages

        return True, "REVIEW_TITLE", pages

    except Exception:
        return False, "CORRUPT_PDF", 0


# ============================================================
# NETWORK REQUEST WITH RETRIES
# ============================================================

def get_with_retry(session, url, params=None):
    for attempt in range(3):
        try:
            response = session.get(
                url,
                params=params,
                timeout=TIMEOUT
            )

            if response.status_code == 429:
                retry_after = response.headers.get(
                    "Retry-After"
                )

                try:
                    delay = float(retry_after)
                except (ValueError, TypeError):
                    delay = 5 * (attempt + 1)

                time.sleep(min(delay, 60))
                continue

            if response.status_code >= 500:
                time.sleep(3 * (attempt + 1))
                continue

            response.raise_for_status()
            return response

        except requests.RequestException:
            if attempt == 2:
                raise

            time.sleep(3 * (attempt + 1))

    raise RuntimeError("Request attempts exhausted")


# ============================================================
# ARXIV DISCOVERY
# ============================================================

def search_arxiv(session, title, year):
    words = re.findall(
        r"[A-Za-z0-9]+",
        str(title)
    )

    # Use significant title words in the search.
    query_title = " ".join(words[:12])

    if not query_title:
        return []

    try:
        response = get_with_retry(
            session,
            ARXIV_API,
            params={
                "search_query": f'ti:"{query_title}"',
                "start": 0,
                "max_results": 10,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
        )

        root = ET.fromstring(response.content)

        candidates = []

        for entry in root.findall("atom:entry", NS):
            entry_title = entry.findtext(
                "atom:title",
                default="",
                namespaces=NS
            )

            score = similarity(
                title,
                entry_title
            )

            if score < TITLE_THRESHOLD:
                continue

            published = entry.findtext(
                "atom:published",
                default="",
                namespaces=NS
            )

            preprint_year = valid_year(
                published[:4]
            )

            # Preprints may precede conference versions.
            if year and preprint_year:
                if preprint_year > year + 1:
                    continue

                if preprint_year < year - 7:
                    continue

            entry_id = entry.findtext(
                "atom:id",
                default="",
                namespaces=NS
            )

            arxiv_id = entry_id.rstrip("/").split("/")[-1]

            if not arxiv_id:
                continue

            pdf_url = (
                "https://arxiv.org/pdf/"
                + arxiv_id
            )

            candidates.append({
                "url": pdf_url,
                "source": "arXiv",
                "matched_title": entry_title,
                "score": score
            })

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return candidates

    except Exception as error:
        print("    arXiv search error:", error)
        return []


# ============================================================
# OPENALEX DISCOVERY
# ============================================================

def search_openalex(session, title, year):
    if not API_KEY:
        return []

    try:
        response = get_with_retry(
            session,
            OPENALEX_API,
            params={
                "api_key": API_KEY,
                "search": title,
                "per_page": 5
            }
        )

        results = response.json().get(
            "results", []
        )

        matches = []

        for work in results:
            work_title = work.get("title") or ""

            score = similarity(
                title,
                work_title
            )

            if score < TITLE_THRESHOLD:
                continue

            work_year = valid_year(
                work.get("publication_year")
            )

            if year and work_year:
                if abs(year - work_year) > 2:
                    continue

            matches.append((score, work))

        if not matches:
            return []

        matches.sort(
            key=lambda x: x[0],
            reverse=True
        )

        work = matches[0][1]
        candidates = []

        for location in work.get("locations") or []:
            if not location.get("is_oa"):
                continue

            pdf = location.get("pdf_url") or ""

            if not pdf or is_media_url(pdf):
                continue

            candidates.append({
                "url": pdf,
                "source": "OpenAlex",
                "matched_title": work.get("title"),
                "score": matches[0][0]
            })

        return candidates

    except Exception as error:
        print("    OpenAlex search error:", error)
        return []


# ============================================================
# PDF DOWNLOADER
# ============================================================

def download_pdf(session, url, destination, title):
    temporary = destination.with_suffix(".part")

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, "INVALID_URL", 0

        if is_media_url(url):
            return False, "MEDIA_URL", 0

        with session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            stream=True
        ) as response:

            if response.status_code in (401, 403):
                return (
                    False,
                    f"HTTP_{response.status_code}",
                    0
                )

            response.raise_for_status()

            size = 0

            with temporary.open("wb") as handle:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    size += len(chunk)

                    if size > MAX_BYTES:
                        return False, "TOO_LARGE", 0

                    handle.write(chunk)

        valid, identity, pages = validate_pdf(
            temporary,
            title
        )

        if not valid:
            return False, identity, pages

        # Only register confidently matched PDFs.
        # Keep uncertain PDFs separately for review.
        if identity == "REVIEW_TITLE":
            quarantine = PDF_DIR / (
                destination.stem + "_REVIEW.pdf"
            )

            temporary.replace(quarantine)

            return False, "REVIEW_TITLE", pages

        temporary.replace(destination)

        return True, identity, pages

    except requests.RequestException as error:
        return False, str(error)[:200], 0

    finally:
        if temporary.exists():
            temporary.unlink()


# ============================================================
# CHECKPOINT HELPERS
# ============================================================

def save_csv(df, path):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary = path.with_suffix(".tmp")

    df.to_csv(
        temporary,
        index=False
    )

    temporary.replace(path)


def log_attempt(logs, record):
    logs.append(record)

    save_csv(
        pd.DataFrame(logs),
        LOG
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    if not MASTER.exists():
        raise FileNotFoundError(MASTER)

    master = pd.read_csv(
        MASTER
    ).fillna("")

    title_col = title_column(master)

    master_titles = master[
        title_col
    ].astype(str)

    if master_titles.map(compact).duplicated().any():
        raise ValueError(
            "Duplicate titles in original master dataset"
        )

    # --------------------------------------------------------
    # Build the 196-paper inventory
    # --------------------------------------------------------

    if OUTPUT.exists():
        inventory = pd.read_csv(
            OUTPUT
        ).fillna("")

        print(
            "Resuming existing 196-paper inventory."
        )

    else:
        old = pd.read_csv(
            OLD_INVENTORY
        ).fillna("")

        old_lookup = {
            compact(row["Title"]): row
            for _, row in old.iterrows()
        }

        rows = []

        for _, paper in master.iterrows():
            title = str(paper[title_col])

            old_record = old_lookup.get(
                compact(title)
            )

            row = {
                "Paper ID": paper_identifier(title),
                "Title": title,
                "Year": paper.get("Year", ""),
                "Conference": paper.get("Conference", ""),
                "Status": "PENDING",
                "Local PDF": "",
                "PDF Identity": "",
                "Acquisition Source": "",
                "Acquisition URL": "",
                "Pages": "",
                "Discovery Status": ""
            }

            if old_record is not None:
                path_string = str(
                    old_record.get(
                        "Local PDF", ""
                    )
                ).strip()

                if path_string:
                    path = Path(path_string)

                    if path.exists():
                        valid, identity, pages = (
                            validate_pdf(path, title)
                        )

                        if valid:
                            row["Status"] = "DOWNLOADED"
                            row["Local PDF"] = str(path)
                            row["PDF Identity"] = identity
                            row["Pages"] = pages
                            row["Acquisition Source"] = (
                                old_record.get(
                                    "Acquisition Source", ""
                                )
                            )
                            row["Acquisition URL"] = (
                                old_record.get(
                                    "Acquisition Detail", ""
                                )
                            )

            rows.append(row)

        inventory = pd.DataFrame(rows)

        save_csv(inventory, OUTPUT)

    if len(inventory) != len(master):
        raise ValueError(
            "Inventory size differs from master dataset."
        )

    # --------------------------------------------------------
    # Load previously discovered OpenAlex URLs
    # --------------------------------------------------------

    discovery_lookup = {}

    if OLD_DISCOVERY.exists():
        discovery = pd.read_csv(
            OLD_DISCOVERY
        ).fillna("")

        discovery_lookup = {
            compact(row["Title"]): row
            for _, row in discovery.iterrows()
        }

    logs = []

    if LOG.exists():
        logs = pd.read_csv(
            LOG
        ).fillna("").to_dict("records")

    previous_failures = set()

    if OLD_ATTEMPTS.exists():
        old_attempts = pd.read_csv(
            OLD_ATTEMPTS
        ).fillna("")

        for _, record in old_attempts.iterrows():
            success = str(
                record.get("Success", "")
            ).casefold()

            if success not in ("true", "1"):
                previous_failures.add((
                    compact(record["Title"]),
                    str(record["URL"])
                ))

    for record in logs:
        if not str(
            record.get("Success", "")
        ).casefold() in ("true", "1"):
            previous_failures.add((
                compact(record.get("Title", "")),
                str(record.get("URL", ""))
            ))

    # --------------------------------------------------------
    # Networking
    # --------------------------------------------------------

    session = requests.Session()

    session.headers.update({
        "User-Agent": "PCS-Acquisition-Research/1.0",
        "Accept": "*/*"
    })

    total = len(inventory)

    # --------------------------------------------------------
    # Process missing PDFs
    # --------------------------------------------------------

    for position, (index, paper) in enumerate(
        inventory.iterrows(),
        start=1
    ):

        title = str(paper["Title"])
        year = valid_year(paper["Year"])

        existing = str(
            paper.get("Local PDF", "")
        ).strip()

        if existing and Path(existing).exists():
            valid, identity, pages = validate_pdf(
                existing, title
            )

            if valid:
                print(
                    f"[{position}/{total}] "
                    f"SKIP: {title}"
                )
                continue

        print(
            f"\n[{position}/{total}] {title}"
        )

        candidates = []

        # ----------------------------------------------------
        # 1. Search arXiv
        # ----------------------------------------------------

        arxiv_candidates = search_arxiv(
            session,
            title,
            year
        )

        candidates.extend(arxiv_candidates)

        time.sleep(ARXIV_DELAY)

        # ----------------------------------------------------
        # 2. Existing OpenAlex sources
        # ----------------------------------------------------

        found = discovery_lookup.get(
            compact(title)
        )

        if found is not None:
            urls = split_urls(
                found.get("PDF Candidates", "")
            )

            for url in urls:
                candidates.append({
                    "url": url,
                    "source": "Existing OpenAlex",
                    "matched_title": title,
                    "score": 1.0
                })

        # ----------------------------------------------------
        # 3. Query OpenAlex for papers not previously searched
        # ----------------------------------------------------

        if found is None and API_KEY:
            candidates.extend(
                search_openalex(
                    session, title, year
                )
            )

            time.sleep(1)

        # ----------------------------------------------------
        # Deduplicate and prioritize source URLs
        # ----------------------------------------------------

        unique = {}

        for candidate in candidates:
            url = str(
                candidate["url"]
            ).strip()

            if not url or is_media_url(url):
                continue

            if url not in unique:
                unique[url] = candidate

        candidates = list(unique.values())

        candidates.sort(
            key=lambda x: source_priority(
                x["url"]
            )
        )

        inventory.at[
            index, "Discovery Status"
        ] = (
            "CANDIDATES_FOUND"
            if candidates
            else "NO_PDF_CANDIDATE"
        )

        # Save discoveries even if downloads fail.
        save_csv(inventory, OUTPUT)

        destination = (
            PDF_DIR / make_filename(title)
        )

        downloaded = False

        for candidate in candidates:
            url = candidate["url"]

            if (
                SKIP_PREVIOUS_FAILURES
                and (compact(title), url)
                in previous_failures
            ):
                print(
                    "  Previously failed; skipping:",
                    url
                )
                continue

            print(
                "  Trying:",
                candidate["source"],
                url
            )

            ok, result, pages = download_pdf(
                session,
                url,
                destination,
                title
            )

            log_attempt(
                logs,
                {
                    "Title": title,
                    "URL": url,
                    "Source": candidate["source"],
                    "Success": ok,
                    "Result": result,
                    "Pages": pages
                }
            )

            if ok:
                inventory.at[
                    index, "Status"
                ] = "DOWNLOADED"

                inventory.at[
                    index, "Local PDF"
                ] = str(destination)

                inventory.at[
                    index, "PDF Identity"
                ] = result

                inventory.at[
                    index, "Pages"
                ] = pages

                inventory.at[
                    index, "Acquisition Source"
                ] = candidate["source"]

                inventory.at[
                    index, "Acquisition URL"
                ] = url

                print(
                    "  SUCCESS:",
                    pages,
                    "pages"
                )

                downloaded = True
                break

            print("  Failed:", result)

            previous_failures.add((
                compact(title), url
            ))

            time.sleep(1)

        if not downloaded:
            inventory.at[
                index, "Status"
            ] = "NOT_ACQUIRED"

        save_csv(inventory, OUTPUT)

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("PDF ACQUISITION SUMMARY: ALL 196 PAPERS")
    print("=" * 60)

    print(inventory["Status"].value_counts())

    acquired = inventory[
        inventory["Status"] == "DOWNLOADED"
    ]

    print(
        "\nAcquired:",
        len(acquired),
        "/", len(inventory)
    )

    print(
        "Remaining:",
        len(inventory) - len(acquired)
    )

    print("\nInventory:", OUTPUT)
    print("Attempt log:", LOG)


if __name__ == "__main__":
    main()
