
import os
import re
import time
from pathlib import Path
from urllib.parse import quote, urlparse

import pandas as pd
import requests


MASTER = Path("pcs_merged_review.csv")
INVENTORY = Path("results/pdf_acquisition_all_196.csv")
OUTPUT = Path("results/acm_alternative_pdf_locations.csv")

API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()

if not API_KEY:
    raise SystemExit("OPENALEX_API_KEY is not set.")

def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()

def clean_doi(value):
    doi = str(value).strip()
    doi = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "", doi, flags=re.I
    )
    return re.sub(r"^doi:\s*", "", doi, flags=re.I)

master = pd.read_csv(MASTER).fillna("")
inventory = pd.read_csv(INVENTORY).fillna("")

missing = inventory[
    inventory["Conference"].isin(["ACM CCS", "ACM ASIACCS"])
    & inventory["Status"].ne("DOWNLOADED")
]

doi_map = {
    normalize(row["Title"]): clean_doi(row["DOI"])
    for _, row in master.iterrows()
}

session = requests.Session()
session.headers["User-Agent"] = "PCS-Literature-Review/1.0"

records = []

for number, (_, paper) in enumerate(missing.iterrows(), 1):
    title = str(paper["Title"])
    doi = doi_map.get(normalize(title), "")

    print(f"[{number}/{len(missing)}] {title}")

    if not doi:
        records.append({
            "Title": title,
            "DOI": "",
            "PDF URL": "",
            "Landing Page": "",
            "Host": "",
            "Status": "MISSING_DOI"
        })
        continue

    try:
        response = session.get(
            "https://api.openalex.org/works/"
            + quote("https://doi.org/" + doi, safe=""),
            params={
                "api_key": API_KEY,
                "select": "id,title,doi,locations"
            },
            timeout=40
        )

        if response.status_code == 429:
            print("API rate limit reached; stopping safely.")
            break

        if response.status_code != 200:
            records.append({
                "Title": title,
                "DOI": doi,
                "PDF URL": "",
                "Landing Page": "",
                "Host": "",
                "Status": f"HTTP_{response.status_code}"
            })
            continue

        work = response.json()
        found = False

        for location in work.get("locations") or []:
            if not location.get("is_oa"):
                continue

            pdf_url = location.get("pdf_url") or ""
            landing = location.get("landing_page_url") or ""

            if not pdf_url:
                continue

            host = urlparse(pdf_url).netloc.lower()

            # We already tested ACM's direct PDF endpoint.
            if host.endswith("dl.acm.org"):
                continue

            found = True

            records.append({
                "Title": title,
                "DOI": doi,
                "PDF URL": pdf_url,
                "Landing Page": landing,
                "Host": host,
                "Status": "PDF_CANDIDATE"
            })

            print("  PDF candidate:", pdf_url)

        if not found:
            records.append({
                "Title": title,
                "DOI": doi,
                "PDF URL": "",
                "Landing Page": "",
                "Host": "",
                "Status": "NO_ALTERNATIVE_PDF"
            })

    except requests.RequestException as error:
        records.append({
            "Title": title,
            "DOI": doi,
            "PDF URL": "",
            "Landing Page": "",
            "Host": "",
            "Status": "ERROR"
        })
        print("  Error:", error)

    finally:
        if records:
            pd.DataFrame(records).to_csv(OUTPUT, index=False)

    time.sleep(1)

print("\n" + "=" * 50)
print("ACM ALTERNATIVE PDF DISCOVERY SUMMARY")
print("=" * 50)

if records:
    result = pd.DataFrame(records)
    print(result["Status"].value_counts())
    print(
        "\nPapers with alternative PDF candidates:",
        result.loc[
            result["Status"] == "PDF_CANDIDATE",
            "Title"
        ].nunique()
    )

print("Saved:", OUTPUT)
