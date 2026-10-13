
import os
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from difflib import SequenceMatcher

import pandas as pd
import requests
import pymupdf


INVENTORY = Path("results/pdf_acquisition_all_196.csv")
DISCOVERY_LOG = Path("results/semantic_scholar_ieee_results.csv")
PDF_DIR = Path("papers/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

API_URL = (
    "https://api.semanticscholar.org"
    "/graph/v1/paper/search"
)

API_KEY = os.environ.get(
    "SEMANTIC_SCHOLAR_API_KEY", ""
).strip()

if not API_KEY:
    raise SystemExit(
        "SEMANTIC_SCHOLAR_API_KEY is missing."
    )

MAX_BYTES = 100 * 1024 * 1024
REQUEST_DELAY = 2.0
TITLE_THRESHOLD = 0.90


def normalize(text):
    return re.sub(
        r"[^a-z0-9]+", " ",
        str(text).casefold()
    ).strip()


def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


def make_filename(title):
    safe = re.sub(
        r"[^A-Za-z0-9]+", "_", title
    ).strip("_")[:70]

    digest = hashlib.sha256(
        title.encode("utf-8")
    ).hexdigest()[:10]

    return f"{safe}_{digest}.pdf"


def validate_pdf(path, title):
    try:
        with path.open("rb") as f:
            if f.read(5) != b"%PDF-":
                return False, "INVALID_PDF", 0

        with pymupdf.open(path) as doc:
            pages = doc.page_count

            if pages < 1:
                return False, "EMPTY_PDF", 0

            text = " ".join(
                doc[i].get_text()
                for i in range(min(pages, 3))
            )

        expected = normalize(title)
        extracted = normalize(text)

        if expected in extracted:
            return True, "TITLE_MATCH", pages

        words = expected.split()
        tokens = extracted.split()

        best = max(
            (
                similarity(
                    expected,
                    " ".join(tokens[i:i + len(words)])
                )
                for i in range(min(len(tokens), 1200))
            ),
            default=0.0
        )

        if best >= 0.88:
            return True, "TITLE_MATCH", pages

        return True, "REVIEW_TITLE", pages

    except Exception as error:
        return False, str(error)[:150], 0


def search_paper(session, title, year):
    response = session.get(
        API_URL,
        params={
            "query": title,
            "limit": 5,
            "fields": (
                "title,year,url,externalIds,"
                "openAccessPdf,isOpenAccess"
            )
        },
        timeout=40
    )

    if response.status_code == 429:
        raise RuntimeError("RATE_LIMITED_429")

    if response.status_code in (401, 403):
        raise RuntimeError(
            f"AUTH_ERROR_{response.status_code}"
        )

    response.raise_for_status()

    matches = []

    for paper in response.json().get("data", []):
        matched_title = paper.get("title") or ""
        score = similarity(title, matched_title)

        if score < TITLE_THRESHOLD:
            continue

        matched_year = paper.get("year")

        if matched_year:
            if abs(int(year) - int(matched_year)) > 2:
                continue

        matches.append((score, paper))

    if not matches:
        return None

    return max(matches, key=lambda x: x[0])[1]


def download_pdf(session, url, destination, title):
    temporary = destination.with_suffix(".part")

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, "INVALID_URL", 0

        if parsed.path.lower().endswith((
            ".mp4", ".zip", ".pptx", ".mov"
        )):
            return False, "NON_PDF_URL", 0

        with session.get(
            url,
            stream=True,
            timeout=60,
            allow_redirects=True
        ) as response:

            if response.status_code in (401, 403):
                return (
                    False,
                    f"HTTP_{response.status_code}",
                    0
                )

            if response.status_code == 429:
                raise RuntimeError("PDF_RATE_LIMITED_429")

            response.raise_for_status()

            total = 0

            with temporary.open("wb") as f:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    total += len(chunk)

                    if total > MAX_BYTES:
                        return False, "TOO_LARGE", 0

                    f.write(chunk)

        valid, identity, pages = validate_pdf(
            temporary, title
        )

        if not valid:
            return False, identity, pages

        if identity != "TITLE_MATCH":
            review_path = (
                PDF_DIR / (destination.stem + "_REVIEW.pdf")
            )
            temporary.replace(review_path)
            return False, "REVIEW_TITLE", pages

        temporary.replace(destination)

        return True, identity, pages

    except requests.RequestException as error:
        return False, str(error)[:200], 0

    finally:
        if temporary.exists():
            temporary.unlink()


def save_progress(inventory, logs):
    inventory.to_csv(INVENTORY, index=False)
    pd.DataFrame(logs).to_csv(
        DISCOVERY_LOG, index=False
    )


def main():
    df = pd.read_csv(INVENTORY).fillna("")

    logs = (
        pd.read_csv(DISCOVERY_LOG).fillna("")
        .to_dict("records")
        if DISCOVERY_LOG.exists()
        else []
    )

    # Avoid repeated searches on later runs.
    attempted = {
        str(record["Title"])
        for record in logs
        if record.get("Status") not in (
            "RATE_LIMITED",
            "ERROR"
        )
    }

    missing = df[
        (df["Conference"] == "IEEE S&P")
        & (df["Status"] != "DOWNLOADED")
    ].copy()

    print("Missing IEEE S&P PDFs:", len(missing))

    session = requests.Session()
    session.headers.update({
        "x-api-key": API_KEY,
        "User-Agent": "PCS-Literature-Review/1.0"
    })

    # Separate download session: no API key sent
    # to external PDF hosts.
    download_session = requests.Session()
    download_session.headers.update({
        "User-Agent": "PCS-Literature-Review/1.0"
    })

    for number, (index, row) in enumerate(
        missing.iterrows(), start=1
    ):
        title = str(row["Title"])
        year = int(float(row["Year"]))

        if title in attempted:
            print("Skipping previously processed:", title)
            continue

        print(f"\n[{number}/{len(missing)}] {title}")

        record = {
            "Title": title,
            "Year": year,
            "Matched Title": "",
            "PDF URL": "",
            "Status": "",
            "Detail": ""
        }

        try:
            paper = search_paper(
                session, title, year
            )

            if paper is None:
                record["Status"] = "NO_MATCH"

            else:
                record["Matched Title"] = (
                    paper.get("title") or ""
                )

                pdf_data = (
                    paper.get("openAccessPdf") or {}
                )

                pdf_url = (
                    pdf_data.get("url") or ""
                ).strip()

                record["PDF URL"] = pdf_url

                if not pdf_url:
                    record["Status"] = "NO_PDF_URL"

                else:
                    destination = (
                        PDF_DIR / make_filename(title)
                    )

                    ok, detail, pages = download_pdf(
                        download_session,
                        pdf_url,
                        destination,
                        title
                    )

                    record["Detail"] = detail

                    if ok:
                        df.at[index, "Status"] = "DOWNLOADED"
                        df.at[index, "Local PDF"] = (
                            str(destination)
                        )
                        df.at[index, "PDF Identity"] = (
                            "TITLE_MATCH"
                        )
                        df.at[index, "Pages"] = pages
                        df.at[
                            index, "Acquisition Source"
                        ] = "Semantic Scholar"
                        df.at[
                            index, "Acquisition URL"
                        ] = pdf_url

                        record["Status"] = "DOWNLOADED"
                        print("  SUCCESS:", pages, "pages")

                    else:
                        record["Status"] = "DOWNLOAD_FAILED"
                        print("  Download failed:", detail)

            if record["Status"] in (
                "NO_MATCH", "NO_PDF_URL"
            ):
                print("  ", record["Status"])

        except Exception as error:
            message = str(error)

            record["Status"] = (
                "RATE_LIMITED"
                if "429" in message
                else "ERROR"
            )
            record["Detail"] = message

            print("  Error:", message)

            logs.append(record)
            save_progress(df, logs)

            if any(term in message for term in (
                "429", "AUTH_ERROR"
            )):
                print(
                    "Stopping safely; rerun to resume."
                )
                break

            time.sleep(REQUEST_DELAY)
            continue

        logs.append(record)
        save_progress(df, logs)
        time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 55)
    print("SEMANTIC SCHOLAR IEEE S&P SUMMARY")
    print("=" * 55)

    if logs:
        latest = pd.DataFrame(logs).drop_duplicates(
            subset=["Title"], keep="last"
        )
        print(latest["Status"].value_counts())

    acquired = (df["Status"] == "DOWNLOADED").sum()

    print("\nTotal PDFs acquired:", acquired)
    print("Remaining PDFs:", len(df) - acquired)
    print("Log:", DISCOVERY_LOG)


if __name__ == "__main__":
    main()
