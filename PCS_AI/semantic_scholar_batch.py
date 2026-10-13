
import os
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

MASTER = Path("pcs_merged_review.csv")

INVENTORY = Path(
    "results/pdf_acquisition_all_196.csv"
)

OUTPUT = Path(
    "results/semantic_scholar_ieee_batch.csv"
)

API = (
    "https://api.semanticscholar.org"
    "/graph/v1/paper/batch"
)

API_KEY = os.getenv(
    "SEMANTIC_SCHOLAR_API_KEY", ""
).strip()

if not API_KEY:
    raise SystemExit(
        "SEMANTIC_SCHOLAR_API_KEY is not configured."
    )


# ============================================================
# HELPERS
# ============================================================

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


def clean_doi(value):
    doi = str(value).strip()

    doi = re.sub(
        r"^https?://(dx\.)?doi\.org/",
        "",
        doi,
        flags=re.IGNORECASE
    )

    doi = re.sub(
        r"^doi:\s*",
        "",
        doi,
        flags=re.IGNORECASE
    )

    return doi.strip()


# ============================================================
# MAIN
# ============================================================

def main():

    master = pd.read_csv(MASTER).fillna("")
    inventory = pd.read_csv(INVENTORY).fillna("")

    missing = inventory[
        (inventory["Conference"] == "IEEE S&P")
        & (inventory["Status"] != "DOWNLOADED")
    ].copy()

    doi_lookup = {
        normalize(row["Title"]): clean_doi(row["DOI"])
        for _, row in master.iterrows()
    }

    records = []

    for _, paper in missing.iterrows():
        title = str(paper["Title"])
        doi = doi_lookup.get(normalize(title), "")

        records.append({
            "Title": title,
            "Year": paper["Year"],
            "DOI": doi,
            "Lookup ID": f"DOI:{doi}" if doi else ""
        })

    df = pd.DataFrame(records)

    if (df["DOI"] == "").any():
        raise ValueError(
            "Some papers are missing DOIs."
        )

    print("Papers to query:", len(df))

    identifiers = df["Lookup ID"].tolist()

    session = requests.Session()
    session.headers.update({
        "x-api-key": API_KEY,
        "User-Agent": "PCS-Literature-Review/1.0",
        "Accept": "application/json"
    })

    response = session.post(
        API,
        params={
            "fields": (
                "title,year,externalIds,"
                "openAccessPdf,isOpenAccess,url"
            )
        },
        json={"ids": identifiers},
        timeout=90
    )

    print("HTTP status:", response.status_code)

    if response.status_code != 200:
        print("Server response:", response.text[:500])
        raise SystemExit(
            "Batch request unsuccessful. "
            "No results were overwritten."
        )

    results = response.json()

    if len(results) != len(df):
        raise ValueError(
            "Unexpected number of batch results."
        )

    output_records = []

    for (_, original), result in zip(
        df.iterrows(), results
    ):

        record = original.to_dict()

        record.update({
            "Matched Title": "",
            "Matched Year": "",
            "Title Similarity": "",
            "Semantic Scholar URL": "",
            "Open PDF URL": "",
            "Status": ""
        })

        if result is None:
            record["Status"] = "NO_MATCH"

        else:
            matched_title = result.get("title") or ""

            score = similarity(
                record["Title"],
                matched_title
            )

            record["Matched Title"] = matched_title
            record["Matched Year"] = (
                result.get("year") or ""
            )
            record["Title Similarity"] = round(score, 4)
            record["Semantic Scholar URL"] = (
                result.get("url") or ""
            )

            if score < 0.90:
                record["Status"] = "REVIEW_MATCH"

            else:
                pdf = (
                    result.get("openAccessPdf") or {}
                )

                pdf_url = (
                    pdf.get("url") or ""
                ).strip()

                record["Open PDF URL"] = pdf_url

                record["Status"] = (
                    "PDF_CANDIDATE"
                    if pdf_url
                    else "NO_PDF_URL"
                )

        output_records.append(record)

    output = pd.DataFrame(output_records)
    output.to_csv(OUTPUT, index=False)

    print("\n" + "=" * 55)
    print("SEMANTIC SCHOLAR BATCH SUMMARY")
    print("=" * 55)

    print(output["Status"].value_counts())

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
