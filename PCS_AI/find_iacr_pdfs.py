
import os
import re
import time
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlparse

import pandas as pd
import requests

INPUT = Path("results/missing_crypto_conference_pdfs.csv")
OUTPUT = Path("results/iacr_pdf_candidates.csv")

API = "https://api.openalex.org/works"
API_KEY = os.getenv("OPENALEX_API_KEY", "").strip()

if not API_KEY:
    raise SystemExit("Please set OPENALEX_API_KEY first.")


def normalize(text):
    return re.sub(
        r"[^a-z0-9]+", " ",
        str(text).casefold()
    ).strip()


def similarity(a, b):
    return SequenceMatcher(
        None, normalize(a), normalize(b)
    ).ratio()


def get_work(session, title):
    response = session.get(
        API,
        params={
            "api_key": API_KEY,
            "search": title,
            "per_page": 10
        },
        timeout=30
    )
    response.raise_for_status()

    matches = []

    for work in response.json().get("results", []):
        score = similarity(title, work.get("title", ""))

        if score >= 0.90:
            matches.append((score, work))

    if not matches:
        return None

    return max(matches, key=lambda x: x[0])[1]


def iacr_urls(work):
    urls = []

    for location in work.get("locations") or []:
        for field in ("pdf_url", "landing_page_url"):
            url = location.get(field) or ""

            if urlparse(url).netloc.lower() == "eprint.iacr.org":
                urls.append(url)

    return list(dict.fromkeys(urls))


def main():
    papers = pd.read_csv(INPUT).fillna("")
    records = []

    session = requests.Session()

    for i, paper in papers.iterrows():
        title = paper["Title"]

        print(f"[{i+1}/{len(papers)}] {title}")

        record = {
            "Title": title,
            "Conference": paper["Conference"],
            "Year": paper["Year"],
            "Matched Title": "",
            "IACR URLs": "",
            "Status": "",
            "Error": ""
        }

        try:
            work = get_work(session, title)

            if work is None:
                record["Status"] = "NO_MATCH"
            else:
                record["Matched Title"] = work.get("title", "")
                urls = iacr_urls(work)
                record["IACR URLs"] = " | ".join(urls)
                record["Status"] = (
                    "IACR_FOUND" if urls else "NO_IACR_LOCATION"
                )

        except Exception as exc:
            record["Status"] = "ERROR"
            record["Error"] = str(exc)

        records.append(record)
        pd.DataFrame(records).to_csv(OUTPUT, index=False)

        print(" ", record["Status"])
        time.sleep(1)

    results = pd.DataFrame(records)

    print("\n" + "=" * 50)
    print("IACR DISCOVERY SUMMARY")
    print("=" * 50)
    print(results["Status"].value_counts())
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
