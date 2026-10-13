
import re
import time
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests


INPUT = Path("results/pdf_acquisition_inventory.csv")
OUTPUT = Path("results/open_access_discovery.csv")

API = "https://api.openalex.org/works"


def normalize(text):
    return re.sub(
        r"[^a-z0-9]+", " ",
        str(text).lower()
    ).strip()


def similarity(a, b):
    return SequenceMatcher(
        None, normalize(a), normalize(b)
    ).ratio()


def lookup_paper(session, title, year):
    response = session.get(
        API,
        params={
            "search": title,
            "per_page": 5
        },
        timeout=30
    )
    response.raise_for_status()

    matches = []

    for work in response.json().get("results", []):
        score = similarity(title, work.get("title", ""))

        if score < 0.92:
            continue

        work_year = work.get("publication_year")

        if year and work_year:
            if abs(int(work_year) - int(year)) > 2:
                continue

        matches.append((score, work))

    if not matches:
        return None

    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1]


def get_oa_locations(work):
    locations = work.get("locations") or []
    candidates = []

    for loc in locations:
        if not loc.get("is_oa"):
            continue

        pdf = loc.get("pdf_url") or ""
        landing = loc.get("landing_page_url") or ""

        # Reject known supplementary/media files.
        if pdf.lower().split("?")[0].endswith(
            (".mp4", ".mov", ".zip", ".pptx")
        ):
            pdf = ""

        # An open-access landing page can still be
        # useful even if no direct PDF is listed.
        if not pdf and not landing:
            continue

        candidates.append({
            "pdf": pdf,
            "landing": landing,
            "source": (
                (loc.get("source") or {}).get("display_name")
                or ""
            )
        })

    # Prefer locations with direct PDF links.
    candidates.sort(
        key=lambda x: bool(x["pdf"]),
        reverse=True
    )

    return candidates


def main():
    df = pd.read_csv(INPUT).fillna("")
    missing = df[df["Status"] != "DOWNLOADED"]

    session = requests.Session()
    session.headers.update({
        "User-Agent": "PCS-Literature-Review/1.0"
    })

    records = []

    print("Papers requiring discovery:", len(missing))

    for position, (_, paper) in enumerate(
        missing.iterrows(), start=1
    ):
        title = str(paper["Title"])
        year = str(paper["Year"]).strip()

        print(f"[{position}/{len(missing)}] {title}")

        record = {
            "Title": title,
            "Conference": paper["Conference"],
            "Year": year,
            "Discovery Status": "",
            "Matched Title": "",
            "OpenAlex ID": "",
            "DOI": "",
            "PDF Candidates": "",
            "Landing Pages": "",
            "Sources": "",
            "Error": ""
        }

        try:
            work = lookup_paper(session, title, year)

            if work is None:
                record["Discovery Status"] = "NO_MATCH"
            else:
                locations = get_oa_locations(work)

                record["Matched Title"] = work.get("title", "")
                record["OpenAlex ID"] = work.get("id", "")
                record["DOI"] = work.get("doi", "")

                record["PDF Candidates"] = " | ".join(
                    x["pdf"] for x in locations if x["pdf"]
                )

                record["Landing Pages"] = " | ".join(
                    x["landing"] for x in locations if x["landing"]
                )

                record["Sources"] = " | ".join(
                    x["source"] for x in locations if x["source"]
                )

                record["Discovery Status"] = (
                    "OA_CANDIDATES"
                    if locations
                    else "NO_OA_LOCATION"
                )

        except Exception as exc:
            record["Discovery Status"] = "ERROR"
            record["Error"] = str(exc)

        records.append(record)

        # Checkpoint after every paper.
        pd.DataFrame(records).to_csv(
            OUTPUT, index=False
        )

        print("  ", record["Discovery Status"])

        time.sleep(0.5)

    results = pd.DataFrame(records)

    print("\n" + "=" * 50)
    print("OPEN-ACCESS DISCOVERY SUMMARY")
    print("=" * 50)
    print(results["Discovery Status"].value_counts())
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
