
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin
from difflib import SequenceMatcher

import pandas as pd
import requests
import pymupdf
from bs4 import BeautifulSoup


INVENTORY = Path("results/pdf_acquisition_all_196.csv")
LOG = Path("results/usenix_download_results.csv")
PDF_DIR = Path("papers/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://www.usenix.org"
MAX_BYTES = 100 * 1024 * 1024

session = requests.Session()
session.headers.update({
    "User-Agent": "PCS-Literature-Review/1.0"
})


def normalize(text):
    return re.sub(
        r"[^a-z0-9]+", " ",
        str(text).casefold()
    ).strip()


def similarity(a, b):
    return SequenceMatcher(
        None, normalize(a), normalize(b)
    ).ratio()


def filename(title):
    safe = re.sub(
        r"[^A-Za-z0-9]+", "_", title
    ).strip("_")[:70]

    digest = hashlib.sha256(
        title.encode("utf-8")
    ).hexdigest()[:8]

    return f"{safe}_{digest}.pdf"


def get_page(url):
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def discover_year(year):
    short_year = str(year)[-2:]

    url = (
        f"{BASE}/conference/"
        f"usenixsecurity{short_year}/technical-sessions"
    )

    print(f"\nReading USENIX {year} proceedings...")

    soup = get_page(url)
    found = {}

    for anchor in soup.find_all("a", href=True):
        title = anchor.get_text(" ", strip=True)

        if not title:
            continue

        link = urljoin(url, anchor["href"])

        if (
            f"/usenixsecurity{short_year}/presentation/"
            not in link
        ):
            continue

        # Keep the most informative title for each URL.
        if (
            link not in found
            or len(title) > len(found[link])
        ):
            found[link] = title

    print("Unique titled presentation links:", len(found))
    return found


def find_pdfs(presentation_url):
    soup = get_page(presentation_url)
    pdfs = []

    for anchor in soup.find_all("a", href=True):
        href = urljoin(
            presentation_url,
            anchor["href"]
        )

        lower = href.lower().split("?")[0]

        if not lower.endswith(".pdf"):
            continue

        if not href.startswith(BASE):
            continue

        if any(word in lower for word in (
            "slides", "appendix", "poster",
            "supplement", "artifact"
        )):
            continue

        pdfs.append(href)

    return list(dict.fromkeys(pdfs))


def download_pdf(url, destination, expected_title):
    temp = destination.with_suffix(".part")

    try:
        with session.get(
            url,
            stream=True,
            timeout=60
        ) as response:

            response.raise_for_status()

            size = 0

            with temp.open("wb") as handle:
                for chunk in response.iter_content(1024 * 1024):
                    if not chunk:
                        continue

                    size += len(chunk)

                    if size > MAX_BYTES:
                        return False, "TOO_LARGE", 0

                    handle.write(chunk)

        with pymupdf.open(temp) as doc:
            pages = doc.page_count

            text = normalize(" ".join(
                doc[i].get_text()
                for i in range(min(3, pages))
            ))

        expected = normalize(expected_title)

        if expected not in text:
            words = expected.split()
            tokens = text.split()

            best = max(
                (
                    similarity(
                        expected,
                        " ".join(tokens[i:i + len(words)])
                    )
                    for i in range(min(len(tokens), 1200))
                ),
                default=0
            )

            if best < 0.88:
                return False, "TITLE_MISMATCH", pages

        temp.replace(destination)

        return True, "TITLE_MATCH", pages

    except Exception as exc:
        return False, str(exc)[:200], 0

    finally:
        if temp.exists():
            temp.unlink()


def main():
    df = pd.read_csv(INVENTORY).fillna("")

    missing = df[
        (df["Conference"] == "USENIX Security")
        & (df["Status"] != "DOWNLOADED")
    ]

    print("Missing USENIX PDFs:", len(missing))

    years = sorted(
        set(int(y) for y in missing["Year"])
    )

    proceedings = {}

    for year in years:
        try:
            proceedings[year] = discover_year(year)
        except Exception as exc:
            print("Proceedings error:", year, exc)
            proceedings[year] = {}

        time.sleep(1)

    records = []

    for number, (index, paper) in enumerate(
        missing.iterrows(), start=1
    ):
        title = str(paper["Title"])
        year = int(paper["Year"])

        print(f"\n[{number}/{len(missing)}] {title}")

        matches = []

        for url, candidate_title in proceedings.get(
            year, {}
        ).items():
            score = similarity(title, candidate_title)

            if score >= 0.85:
                matches.append(
                    (score, url, candidate_title)
                )

        matches.sort(reverse=True)

        record = {
            "Title": title,
            "Year": year,
            "Presentation URL": "",
            "PDF URL": "",
            "Status": "NOT_FOUND",
            "Detail": ""
        }

        for score, page_url, candidate_title in matches[:5]:
            print(
                f"  Matched presentation ({score:.3f}):",
                candidate_title
            )

            try:
                pdf_urls = find_pdfs(page_url)
            except Exception as exc:
                record["Detail"] = str(exc)
                continue

            for pdf_url in pdf_urls:
                destination = PDF_DIR / filename(title)

                ok, detail, pages = download_pdf(
                    pdf_url,
                    destination,
                    title
                )

                if ok:
                    df.at[index, "Status"] = "DOWNLOADED"
                    df.at[index, "Local PDF"] = str(destination)
                    df.at[index, "PDF Identity"] = "TITLE_MATCH"
                    df.at[index, "Pages"] = pages
                    df.at[index, "Acquisition Source"] = "USENIX"
                    df.at[index, "Acquisition URL"] = pdf_url

                    record.update({
                        "Presentation URL": page_url,
                        "PDF URL": pdf_url,
                        "Status": "DOWNLOADED",
                        "Detail": f"{pages} pages"
                    })

                    print("  SUCCESS:", pages, "pages")
                    break

                record["Detail"] = detail

            if record["Status"] == "DOWNLOADED":
                break

        if record["Status"] != "DOWNLOADED":
            print("  Not acquired automatically")

        records.append(record)

        # Preserve progress after every paper.
        df.to_csv(INVENTORY, index=False)
        pd.DataFrame(records).to_csv(LOG, index=False)

        time.sleep(0.5)

    print("\n" + "=" * 55)
    print("USENIX PDF DOWNLOAD SUMMARY")
    print("=" * 55)

    print(pd.DataFrame(records)["Status"].value_counts())

    total = (df["Status"] == "DOWNLOADED").sum()

    print("\nTotal PDFs acquired:", total)
    print("Remaining:", len(df) - total)
    print("Log:", LOG)


if __name__ == "__main__":
    main()
