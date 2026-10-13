
import os
import re
import time
import hashlib
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlparse, unquote

import pandas as pd
import requests
import pymupdf


ROOT = Path(".")
CHECKLIST = ROOT / "results/final_15_pdf_checklist.csv"
INVENTORY = ROOT / "results/pdf_acquisition_all_196.csv"
LOG = ROOT / "results/final_15_acquisition_log.csv"
PDF_DIR = ROOT / "papers/pdfs"

PDF_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 100 * 1024 * 1024
DELAY = 1.5

# Independently identified public PDF sources.
# These are candidate URLs, not guaranteed successful downloads.
KNOWN_SOURCES = {
    "10.14722/ndss.2026.241861": [
        "https://www.ndss-symposium.org/wp-content/uploads/2026-f1861-paper.pdf",
    ],
    "10.1007/978-3-031-38545-2_7": [
        "https://eprint.iacr.org/2021/1043.pdf",
    ],
    "10.1007/978-3-031-68403-6_8": [
        "https://eprint.iacr.org/2024/1293.pdf",
    ],
    "10.1007/978-3-031-91134-7_8": [
        "https://eprint.iacr.org/2024/1586.pdf",
    ],
}

session = requests.Session()
session.headers.update({
    "User-Agent": "PCS-Academic-Review/1.0"
})


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = text.replace("\u00ad", "")
    text = text.casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def clean_doi(value):
    doi = str(value).strip()
    doi = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        doi,
        flags=re.I
    )
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return doi.lower()


def filename(title):
    stem = re.sub(
        r"[^A-Za-z0-9]+", "_", str(title)
    ).strip("_")[:80]

    digest = hashlib.sha256(
        str(title).encode()
    ).hexdigest()[:8]

    return f"{stem}_{digest}.pdf"


def title_score(expected, text):
    a = normalize(expected)
    b = normalize(text)

    if a in b:
        return 1.0

    expected_words = a.split()
    words = b.split()
    n = len(expected_words)

    if not words or not n:
        return 0.0

    # Examine front matter, allowing minor variations
    # and PDF extraction artifacts.
    return max(
        (
            SequenceMatcher(
                None, a, " ".join(words[i:i+n])
            ).ratio()
            for i in range(
                min(max(1, len(words) - n + 1), 800)
            )
        ),
        default=0.0
    )


def validate_pdf(path, title):
    with path.open("rb") as f:
        if f.read(5) != b"%PDF-":
            return False, 0, 0.0, "NOT_PDF"

    with pymupdf.open(path) as doc:
        pages = doc.page_count

        if pages == 0:
            return False, 0, 0.0, "EMPTY_PDF"

        text = " ".join(
            doc[i].get_text("text")
            for i in range(min(3, pages))
        )

    score = title_score(title, text)

    # Strict threshold: avoid registering wrong papers.
    return (
        score >= 0.90,
        pages,
        score,
        "TITLE_MATCH" if score >= 0.90 else "TITLE_REVIEW"
    )


def semantic_scholar_candidates(rows):
    key = os.getenv(
        "SEMANTIC_SCHOLAR_API_KEY", ""
    ).strip()

    if not key:
        print("Semantic Scholar key absent; skipping batch.")
        return {}

    ids = [
        "DOI:" + clean_doi(row["DOI"])
        for _, row in rows.iterrows()
    ]

    try:
        response = session.post(
            "https://api.semanticscholar.org/graph/v1/paper/batch",
            headers={"x-api-key": key},
            params={
                "fields": "title,externalIds,openAccessPdf"
            },
            json={"ids": ids},
            timeout=60
        )

        if response.status_code != 200:
            print(
                "Semantic Scholar batch unavailable:",
                response.status_code
            )
            return {}

        output = {}

        for (_, row), paper in zip(
            rows.iterrows(), response.json()
        ):
            if not paper:
                continue

            if title_score(
                row["Title"],
                paper.get("title", "")
            ) < 0.90:
                continue

            pdf = paper.get("openAccessPdf") or {}
            url = (pdf.get("url") or "").strip()

            if url:
                output[clean_doi(row["DOI"])] = [url]

        return output

    except (requests.RequestException, ValueError) as exc:
        print("Semantic Scholar error:", exc)
        return {}


def crossref_candidates(doi):
    try:
        response = session.get(
            "https://api.crossref.org/works/" + doi,
            timeout=30
        )

        if response.status_code != 200:
            return []

        links = response.json().get(
            "message", {}
        ).get("link", [])

        return [
            item["URL"]
            for item in links
            if "pdf" in str(
                item.get("content-type", "")
            ).lower()
            and item.get("URL")
        ]

    except (requests.RequestException, ValueError):
        return []


def openalex_candidates(doi):
    key = os.getenv("OPENALEX_API_KEY", "").strip()

    if not key:
        return []

    try:
        response = session.get(
            "https://api.openalex.org/works/"
            "https://doi.org/" + doi,
            params={"api_key": key},
            timeout=30
        )

        if response.status_code != 200:
            return []

        work = response.json()
        urls = []

        for loc in work.get("locations") or []:
            url = loc.get("pdf_url") or ""

            if url:
                urls.append(url)

        return urls

    except (requests.RequestException, ValueError):
        return []


def unique_urls(urls):
    result = []
    seen = set()

    for url in urls:
        url = str(url).strip()

        if not url or url in seen:
            continue

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            continue

        if parsed.hostname is None:
            continue

        seen.add(url)
        result.append(url)

    return result


def download(url, destination, title):
    temp = destination.with_suffix(".part")

    try:
        with session.get(
            url,
            stream=True,
            timeout=50,
            allow_redirects=True
        ) as response:

            if response.status_code in (401, 403, 429):
                return (
                    False,
                    f"HTTP_{response.status_code}",
                    0,
                    0.0
                )

            response.raise_for_status()

            size = 0

            with temp.open("wb") as out:
                for chunk in response.iter_content(
                    1024 * 1024
                ):
                    if not chunk:
                        continue

                    size += len(chunk)

                    if size > MAX_BYTES:
                        return False, "TOO_LARGE", 0, 0.0

                    out.write(chunk)

        valid, pages, score, reason = validate_pdf(
            temp, title
        )

        if not valid:
            return False, reason, pages, score

        temp.replace(destination)

        return True, "TITLE_MATCH", pages, score

    except Exception as exc:
        return (
            False,
            str(exc)[:160],
            0,
            0.0
        )

    finally:
        if temp.exists():
            temp.unlink()


def main():
    checklist = pd.read_csv(CHECKLIST).fillna("")
    inventory = pd.read_csv(INVENTORY).fillna("")

    if len(checklist) != 15:
        raise ValueError(
            f"Expected 15 papers, found {len(checklist)}"
        )

    existing = (
        pd.read_csv(LOG).fillna("").to_dict("records")
        if LOG.exists()
        else []
    )

    # Don't retry URL failures from previous runs.
    attempted = {
        (str(r["Title"]), str(r["URL"]))
        for r in existing
        if str(r.get("URL", "")).strip()
    }

    s2_candidates = semantic_scholar_candidates(
        checklist
    )

    records = existing[:]

    for number, (_, paper) in enumerate(
        checklist.iterrows(), 1
    ):
        title = str(paper["Title"])
        doi = clean_doi(paper["DOI"])

        print(f"\n[{number}/15] {title}")

        matches = (
            inventory["Title"].map(normalize)
            == normalize(title)
        )

        if matches.sum() != 1:
            print("  Inventory match error")
            continue

        index = inventory.index[matches][0]

        if inventory.at[index, "Status"] == "DOWNLOADED":
            print("  Already registered; skipping.")
            continue

        urls = unique_urls(
            KNOWN_SOURCES.get(doi, [])
            + s2_candidates.get(doi, [])
            + crossref_candidates(doi)
            + openalex_candidates(doi)
        )

        destination = PDF_DIR / filename(title)

        if destination.exists():
            print("  Destination already exists; inspect manually.")
            continue

        success = False

        for url in urls:
            if (title, url) in attempted:
                continue

            # Avoid retrying the known blocked IACR
            # host repeatedly after one HTTP 403.
            print("  Trying:", url)

            ok, reason, pages, score = download(
                url, destination, title
            )

            record = {
                "Title": title,
                "DOI": doi,
                "URL": url,
                "Status": (
                    "DOWNLOADED" if ok else reason
                ),
                "Pages": pages,
                "Title Score": round(score, 4)
            }

            records.append(record)
            attempted.add((title, url))

            pd.DataFrame(records).to_csv(
                LOG, index=False
            )

            if ok:
                inventory.at[index, "Status"] = "DOWNLOADED"
                inventory.at[index, "Local PDF"] = str(destination)
                inventory.at[index, "PDF Identity"] = "TITLE_MATCH"
                inventory.at[index, "Pages"] = pages
                inventory.at[index, "Acquisition Source"] = (
                    "Public automated download"
                )
                inventory.at[index, "Acquisition URL"] = url

                inventory.to_csv(INVENTORY, index=False)

                print("  SUCCESS:", pages, "pages")
                success = True
                break

            print("  Failed:", reason)
            time.sleep(DELAY)

        if not success:
            print("  Not acquired automatically.")

    total = inventory["Status"].eq("DOWNLOADED").sum()

    print("\n" + "=" * 55)
    print("FINAL 15 PDF ACQUISITION SUMMARY")
    print("=" * 55)

    print("Total PDFs acquired:", total)
    print("Remaining overall:", len(inventory) - total)

    remaining = inventory[
        inventory["Status"] != "DOWNLOADED"
    ]

    print("\nRemaining by conference:")
    print(
        remaining["Conference"]
        .value_counts()
        .to_string()
    )

    print("\nLog:", LOG)
    print("Inventory:", INVENTORY)


if __name__ == "__main__":
    main()
