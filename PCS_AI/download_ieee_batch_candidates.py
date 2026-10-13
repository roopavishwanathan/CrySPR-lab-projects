
import hashlib
import re
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlparse

import pandas as pd
import pymupdf
import requests


INVENTORY = Path("results/pdf_acquisition_all_196.csv")
CANDIDATES = Path("results/semantic_scholar_ieee_batch.csv")
LOG = Path("results/ieee_batch_download_log.csv")
PDF_DIR = Path("papers/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 100 * 1024 * 1024


def normalize(text):
    return re.sub(
        r"[^a-z0-9]+", " ", str(text).lower()
    ).strip()


def similarity(a, b):
    return SequenceMatcher(
        None, normalize(a), normalize(b)
    ).ratio()


def filename(title):
    safe = re.sub(
        r"[^A-Za-z0-9]+", "_", title
    ).strip("_")[:65]

    digest = hashlib.sha256(
        title.encode()
    ).hexdigest()[:8]

    return f"{safe}_{digest}.pdf"


def check_title(pdf_path, title):
    with pymupdf.open(pdf_path) as doc:
        pages = doc.page_count

        if pages < 1:
            return False, pages

        text = normalize(" ".join(
            doc[i].get_text()
            for i in range(min(3, pages))
        ))

    expected = normalize(title)

    if expected in text:
        return True, pages

    # Allow line breaks, punctuation and minor
    # differences between metadata and PDF titles.
    n = len(expected.split())
    words = text.split()

    best = max(
        (
            similarity(
                expected,
                " ".join(words[i:i + n])
            )
            for i in range(min(len(words), 1000))
        ),
        default=0
    )

    return best >= 0.90, pages


inventory = pd.read_csv(INVENTORY).fillna("")
candidates = pd.read_csv(CANDIDATES).fillna("")

candidates = candidates[
    candidates["Status"] == "PDF_CANDIDATE"
]

print("PDF candidates:", len(candidates))

logs = []
session = requests.Session()
session.headers["User-Agent"] = "PCS-Literature-Review/1.0"

for _, paper in candidates.iterrows():

    title = str(paper["Title"])
    url = str(paper["Open PDF URL"]).strip()

    print("\nPaper:", title)
    print("PDF URL:", url)

    record = {
        "Title": title,
        "PDF URL": url,
        "Status": "",
        "Pages": ""
    }

    match = (
        (inventory["Title"].map(normalize) == normalize(title))
        & (inventory["Conference"] == "IEEE S&P")
    )

    if match.sum() != 1:
        record["Status"] = "INVENTORY_MATCH_ERROR"
        logs.append(record)
        continue

    index = inventory.index[match][0]

    if inventory.at[index, "Status"] == "DOWNLOADED":
        record["Status"] = "ALREADY_DOWNLOADED"
        logs.append(record)
        continue

    destination = PDF_DIR / filename(title)
    temporary = destination.with_suffix(".part")

    try:
        if urlparse(url).scheme not in ("http", "https"):
            raise ValueError("Invalid PDF URL")

        response = session.get(
            url, timeout=60, stream=True
        )
        response.raise_for_status()

        total = 0

        with temporary.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue

                total += len(chunk)

                if total > MAX_BYTES:
                    raise ValueError("PDF exceeds size limit")

                output.write(chunk)

        with temporary.open("rb") as file:
            if file.read(5) != b"%PDF-":
                raise ValueError("Response is not a PDF")

        matched, pages = check_title(
            temporary, title
        )

        record["Pages"] = pages

        if not matched:
            record["Status"] = "TITLE_REVIEW_REQUIRED"
            print("  Title mismatch; not registered.")
            continue

        temporary.replace(destination)

        inventory.at[index, "Status"] = "DOWNLOADED"
        inventory.at[index, "Local PDF"] = str(destination)
        inventory.at[index, "PDF Identity"] = "TITLE_MATCH"
        inventory.at[index, "Pages"] = pages
        inventory.at[index, "Acquisition Source"] = (
            "Semantic Scholar OA URL"
        )
        inventory.at[index, "Acquisition URL"] = url

        record["Status"] = "DOWNLOADED"
        print("  SUCCESS:", pages, "pages")

    except Exception as error:
        record["Status"] = "FAILED"
        record["Error"] = str(error)[:250]
        print("  ERROR:", error)

    finally:
        if temporary.exists():
            temporary.unlink()

        logs.append(record)
        inventory.to_csv(INVENTORY, index=False)
        pd.DataFrame(logs).to_csv(LOG, index=False)


print("\n" + "=" * 50)
print("IEEE S&P PDF DOWNLOAD SUMMARY")
print("=" * 50)

print(pd.DataFrame(logs)["Status"].value_counts())

acquired = (inventory["Status"] == "DOWNLOADED").sum()

print("\nTotal PDFs acquired:", acquired)
print("Remaining:", len(inventory) - acquired)
print("Log:", LOG)
