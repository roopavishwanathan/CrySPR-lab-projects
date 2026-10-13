
import hashlib
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

import fitz
import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

DISCOVERY = Path(
    "results/open_access_discovery_recovered.csv"
)

INVENTORY = Path(
    "results/pdf_acquisition_inventory.csv"
)

OUTPUT = Path(
    "results/pdf_acquisition_inventory_openalex.csv"
)

ATTEMPTS_LOG = Path(
    "results/openalex_pdf_download_attempts.csv"
)

PDF_DIR = Path("papers/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 100 * 1024 * 1024
TIMEOUT = 45
REQUEST_DELAY = 1.0


# ============================================================
# TITLE HELPERS
# ============================================================

def normalize(title):
    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(title).casefold()
    )


def normalize_words(text):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(text).casefold()
    ).strip()


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


# ============================================================
# DOWNLOAD SOURCE PRIORITY
# ============================================================

def source_priority(url):
    domain = urlparse(url).netloc.lower()

    if domain in ("arxiv.org", "export.arxiv.org"):
        return 0

    if domain == "eprint.iacr.org":
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


def sorted_pdf_urls(raw_urls):
    urls = [
        url.strip()
        for url in str(raw_urls).split(" | ")
        if url.strip()
    ]

    # Reject multimedia/supplementary links.
    forbidden = (
        ".mp4", ".mov", ".avi",
        ".zip", ".pptx", ".mp3"
    )

    urls = [
        url for url in urls
        if not urlparse(url).path.lower().endswith(
            forbidden
        )
    ]

    # Remove duplicate URLs without changing identity.
    urls = list(dict.fromkeys(urls))

    # Try arXiv and repositories first.
    urls.sort(key=source_priority)

    return urls


# ============================================================
# PDF VALIDATION
# ============================================================

def validate_pdf(path, expected_title=None):
    try:
        with path.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                return False, "Invalid PDF signature", ""

        with fitz.open(path) as document:
            if document.page_count < 1:
                return False, "PDF has no pages", ""

            first_pages = "\n".join(
                document[i].get_text()
                for i in range(min(2, document.page_count))
            )

            if len(first_pages.strip()) < 30:
                return (
                    False,
                    "Insufficient extractable text",
                    ""
                )

            identity = "NOT_CHECKED"

            if expected_title:
                expected = normalize_words(expected_title)
                extracted = normalize_words(first_pages)

                # Exact normalized title somewhere near the start.
                if expected in extracted:
                    identity = "TITLE_MATCH"
                else:
                    # Fuzzy comparison of nearby text chunks.
                    words = expected.split()
                    page_words = extracted.split()
                    target_length = len(words)

                    best_score = 0.0

                    if target_length:
                        for start in range(
                            0,
                            min(len(page_words), 1200)
                        ):
                            window = " ".join(
                                page_words[
                                    start:start + target_length
                                ]
                            )

                            score = SequenceMatcher(
                                None,
                                expected,
                                window
                            ).ratio()

                            best_score = max(
                                best_score,
                                score
                            )

                    identity = (
                        "TITLE_MATCH"
                        if best_score >= 0.88
                        else "REVIEW_TITLE"
                    )

            details = f"{document.page_count} pages"

            return True, details, identity

    except Exception as error:
        return False, str(error), ""


# ============================================================
# PDF DOWNLOADER
# ============================================================

def download_pdf(session, url, destination, title):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False, "Invalid URL", ""

    temporary = destination.with_suffix(".part")

    try:
        with session.get(
            url,
            stream=True,
            timeout=TIMEOUT,
            allow_redirects=True
        ) as response:

            if response.status_code in (401, 403):
                return (
                    False,
                    f"HTTP {response.status_code}",
                    ""
                )

            response.raise_for_status()

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:
                try:
                    if int(content_length) > MAX_BYTES:
                        return (
                            False,
                            "File exceeds 100 MB",
                            ""
                        )
                except ValueError:
                    pass

            total = 0

            with temporary.open("wb") as output:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    total += len(chunk)

                    if total > MAX_BYTES:
                        return (
                            False,
                            "File exceeds 100 MB",
                            ""
                        )

                    output.write(chunk)

        valid, details, identity = validate_pdf(
            temporary,
            expected_title=title
        )

        if not valid:
            return False, details, ""

        # Retain readable PDFs even if title needs review.
        # Such PDFs are NOT marked as identity-verified.
        temporary.replace(destination)

        return True, details, identity

    except requests.RequestException as error:
        return False, str(error), ""

    finally:
        if temporary.exists():
            temporary.unlink()


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():

    if not INVENTORY.exists():
        raise FileNotFoundError(INVENTORY)

    if not DISCOVERY.exists():
        raise FileNotFoundError(DISCOVERY)

    discovery = pd.read_csv(DISCOVERY).fillna("")

    # Resume from saved output if available.
    source = OUTPUT if OUTPUT.exists() else INVENTORY
    inventory = pd.read_csv(source).fillna("")

    if inventory["Title"].map(normalize).duplicated().any():
        raise ValueError(
            "Duplicate titles found in inventory"
        )

    if discovery["Title"].map(normalize).duplicated().any():
        raise ValueError(
            "Duplicate titles found in discovery records"
        )

    lookup = {
        normalize(row["Title"]): row
        for _, row in discovery.iterrows()
    }

    for column in [
        "Acquisition Source",
        "Acquisition Detail",
        "PDF Identity"
    ]:
        if column not in inventory.columns:
            inventory[column] = ""

    attempts = []

    if ATTEMPTS_LOG.exists():
        attempts = (
            pd.read_csv(ATTEMPTS_LOG)
            .fillna("")
            .to_dict("records")
        )

    # Cache failed attempts to avoid repeating HTTP 403s.
    previously_failed = {
        (
            str(record.get("Title", "")),
            str(record.get("URL", ""))
        )
        for record in attempts
        if str(record.get("Success", "")).lower()
        not in ("true", "1")
    }

    session = requests.Session()
    session.headers.update({
        "User-Agent": "PCS-Literature-Review/1.0",
        "Accept": "application/pdf,*/*"
    })

    candidates = []

    for index, paper in inventory.iterrows():
        existing = str(
            paper.get("Local PDF", "")
        ).strip()

        # Preserve existing valid PDFs.
        if existing:
            path = Path(existing)

            if path.exists():
                valid, _, identity = validate_pdf(
                    path,
                    expected_title=str(paper["Title"])
                )

                if valid:
                    if not str(
                        inventory.at[index, "PDF Identity"]
                    ).strip():
                        inventory.at[
                            index, "PDF Identity"
                        ] = identity

                    continue

        title = str(paper["Title"])
        found = lookup.get(normalize(title))

        if found is None:
            continue

        urls = sorted_pdf_urls(
            found.get("PDF Candidates", "")
        )

        if urls:
            candidates.append((index, title, urls))

    print(
        "Papers with PDF candidates:",
        len(candidates)
    )

    for position, (index, title, urls) in enumerate(
        candidates,
        start=1
    ):
        print(
            f"\n[{position}/{len(candidates)}] "
            f"{title}"
        )

        destination = PDF_DIR / make_filename(title)

        # Handle an orphaned valid PDF from interrupted runs.
        if destination.exists():
            valid, details, identity = validate_pdf(
                destination,
                expected_title=title
            )

            if valid:
                inventory.at[index, "Local PDF"] = (
                    str(destination)
                )

                inventory.at[index, "Status"] = (
                    "DOWNLOADED"
                )

                inventory.at[
                    index, "PDF Identity"
                ] = identity

                print(
                    "  Recovered existing PDF:",
                    details,
                    identity
                )

                inventory.to_csv(
                    OUTPUT,
                    index=False
                )

                continue

        success = False

        for url in urls:

            if (title, url) in previously_failed:
                print(
                    "  Skipping previously failed URL:",
                    url
                )
                continue

            print("  Trying:", url)

            ok, detail, identity = download_pdf(
                session,
                url,
                destination,
                title
            )

            attempts.append({
                "Title": title,
                "URL": url,
                "Success": ok,
                "Detail": detail,
                "PDF Identity": identity
            })

            # Checkpoint the attempt log immediately.
            pd.DataFrame(attempts).to_csv(
                ATTEMPTS_LOG,
                index=False
            )

            if ok:
                inventory.at[index, "Local PDF"] = (
                    str(destination)
                )

                inventory.at[index, "Status"] = (
                    "DOWNLOADED"
                )

                inventory.at[
                    index, "Acquisition Source"
                ] = urlparse(url).netloc

                inventory.at[
                    index, "Acquisition Detail"
                ] = url

                inventory.at[
                    index, "PDF Identity"
                ] = identity

                print(
                    "  SUCCESS:",
                    detail,
                    "|",
                    identity
                )

                success = True
                break

            previously_failed.add((title, url))

            print("  FAILED:", detail)

            time.sleep(REQUEST_DELAY)

        if not success:
            print(
                "  No valid PDF obtained"
            )

        # Checkpoint after every paper.
        inventory.to_csv(
            OUTPUT,
            index=False
        )

        time.sleep(REQUEST_DELAY)

    inventory.to_csv(
        OUTPUT,
        index=False
    )

    print("\n" + "=" * 60)
    print("UPDATED PDF ACQUISITION SUMMARY")
    print("=" * 60)

    print(
        inventory["Status"].value_counts()
    )

    print("\nPDF identity status:")

    acquired = inventory[
        inventory["Status"] == "DOWNLOADED"
    ]

    print(
        acquired["PDF Identity"].value_counts(
            dropna=False
        )
    )

    print(
        "\nPDFs registered:",
        len(acquired)
    )

    print(
        "Remaining papers:",
        len(inventory) - len(acquired)
    )

    print("\nSaved inventory:", OUTPUT)
    print("Saved attempt log:", ATTEMPTS_LOG)


if __name__ == "__main__":
    main()
