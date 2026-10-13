

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests


INPUT = Path("results/fulltext_155_inventory.csv")
OUTPUT = Path("results/pdf_download_status.csv")
PDF_DIR = Path("papers/pdfs")

PDF_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT = 30
MAX_SIZE = 100 * 1024 * 1024  # 100 MB

HEADERS = {
    "User-Agent": "PCS-Literature-Review/1.0"
}


def make_filename(title):
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", title)
    safe = safe.strip("_")[:75]

    identifier = hashlib.sha256(
        title.encode("utf-8")
    ).hexdigest()[:10]

    return f"{safe}_{identifier}.pdf"


def is_pdf(path):
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def download_pdf(url, destination):
    temporary = destination.with_suffix(".part")

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return "INVALID_URL", ""

        if parsed.path.lower().endswith(
            (".mp4", ".zip", ".mov")
        ):
            return "NON_PDF_URL", ""

        with requests.get(
            url,
            headers=HEADERS,
            stream=True,
            timeout=TIMEOUT,
            allow_redirects=True
        ) as response:

            if response.status_code in (401, 403):
                return "ACCESS_RESTRICTED", str(response.status_code)

            response.raise_for_status()

            total = 0

            with temporary.open("wb") as f:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    total += len(chunk)

                    if total > MAX_SIZE:
                        return "TOO_LARGE", "Exceeded 100 MB"

                    f.write(chunk)

        if not is_pdf(temporary):
            return "NOT_A_PDF", "Response did not contain a PDF"

        temporary.replace(destination)

        return "DOWNLOADED", ""

    except requests.RequestException as error:
        return "DOWNLOAD_ERROR", str(error)

    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    df = pd.read_csv(INPUT).fillna("")

    required = {"Title", "PDF URL"}
    if not required.issubset(df.columns):
        raise ValueError(
            "Input must contain Title and PDF URL columns."
        )

    records = []

    for position, (_, paper) in enumerate(
        df.iterrows(), start=1
    ):
        title = str(paper["Title"])
        url = str(paper["PDF URL"]).strip()

        filename = make_filename(title)
        destination = PDF_DIR / filename

        print(f"[{position}/{len(df)}] {title}")

        if destination.exists() and is_pdf(destination):
            status, detail = "ALREADY_EXISTS", ""

        elif not url:
            status, detail = "MISSING_URL", ""

        else:
            status, detail = download_pdf(
                url, destination
            )
            time.sleep(1)

        record = {
            "Title": title,
            "Conference": paper.get("Conference", ""),
            "Year": paper.get("Year", ""),
            "PDF URL": url,
            "Local PDF": (
                str(destination)
                if status in ("DOWNLOADED", "ALREADY_EXISTS")
                else ""
            ),
            "Status": status,
            "Detail": detail
        }

        records.append(record)

        pd.DataFrame(records).to_csv(
            OUTPUT,
            index=False
        )

        print("  Status:", status)

    results = pd.DataFrame(records)

    print("\n" + "=" * 60)
    print("PDF DOWNLOAD SUMMARY")
    print("=" * 60)
    print(results["Status"].value_counts())
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
