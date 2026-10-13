
import os
import re
import time
import random
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

INPUT = Path("results/open_access_discovery.csv")
OUTPUT = Path("results/open_access_discovery_recovered.csv")

API_URL = "https://api.openalex.org/works"

API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()

MAX_ATTEMPTS = 4
REQUEST_DELAY = 1.0
TITLE_THRESHOLD = 0.92

RETRYABLE_ERRORS = (
    r"401|Unauthorized|AUTHENTICATION_FAILED|"
    r"400|Bad Request|"
    r"429|Too Many Requests|RATE_LIMIT"
)

MEDIA_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".zip",
    ".pptx",
    ".mp3",
    ".avi"
)

if not API_KEY:
    raise SystemExit(
        "ERROR: OPENALEX_API_KEY is not set.\n"
        "Please export your API key before running."
    )


# ============================================================
# TITLE NORMALIZATION AND MATCHING
# ============================================================

def normalize_title(title):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(title).casefold()
    ).strip()


def title_similarity(a, b):
    return SequenceMatcher(
        None,
        normalize_title(a),
        normalize_title(b)
    ).ratio()


def select_matching_work(results, title, year):
    candidates = []

    for work in results:
        matched_title = work.get("title") or ""

        score = title_similarity(
            title,
            matched_title
        )

        if score < TITLE_THRESHOLD:
            continue

        work_year = work.get("publication_year")

        if work_year and str(year).strip():
            try:
                difference = abs(
                    int(float(year)) - int(work_year)
                )

                if difference > 2:
                    continue

            except (ValueError, TypeError):
                pass

        candidates.append((score, work))

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# OPEN-ACCESS LOCATION EXTRACTION
# ============================================================

def is_media_url(url):
    path = str(url).lower().split("?")[0]
    return path.endswith(MEDIA_EXTENSIONS)


def extract_oa_locations(work):
    locations = []
    seen = set()

    for location in work.get("locations") or []:
        if not location.get("is_oa"):
            continue

        pdf = location.get("pdf_url") or ""
        landing = location.get("landing_page_url") or ""

        if is_media_url(pdf):
            pdf = ""

        if is_media_url(landing):
            landing = ""

        if not pdf and not landing:
            continue

        identity = (pdf, landing)

        if identity in seen:
            continue

        seen.add(identity)

        source = location.get("source") or {}

        locations.append({
            "pdf": pdf,
            "landing": landing,
            "source": (
                source.get("display_name") or ""
            )
        })

    locations.sort(
        key=lambda item: bool(item["pdf"]),
        reverse=True
    )

    return locations


# ============================================================
# QUERY PREPARATION
# ============================================================

def simplify_query(title):
    """
    Remove punctuation that may cause problems with
    scholarly-index search queries.
    """
    return re.sub(
        r"\s+",
        " ",
        re.sub(
            r"[^A-Za-z0-9 ]+",
            " ",
            str(title)
        )
    ).strip()


# ============================================================
# AUTHENTICATED OPENALEX REQUEST
# ============================================================

def request_openalex(session, query):
    for attempt in range(MAX_ATTEMPTS):

        try:
            response = session.get(
                API_URL,
                params={
                    "api_key": API_KEY,
                    "search": query,
                    "per_page": 5
                },
                timeout=30
            )

        except requests.RequestException as exc:
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(
                    f"NETWORK_ERROR: {exc}"
                ) from exc

            delay = min(2 ** (attempt + 1), 30)

            print(
                f"    Network error; retrying "
                f"in {delay}s"
            )

            time.sleep(delay)
            continue

        # Stop immediately on invalid authentication.
        if response.status_code == 401:
            raise RuntimeError(
                "AUTHENTICATION_FAILED: "
                + response.text[:200]
            )

        if response.status_code == 403:
            raise RuntimeError(
                "ACCESS_FORBIDDEN: "
                + response.text[:200]
            )

        if response.status_code == 400:
            raise ValueError(
                "BAD_REQUEST_400: "
                + response.text[:200]
            )

        if response.status_code == 429:
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError("RATE_LIMIT_429")

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                delay = (
                    float(retry_after)
                    if retry_after
                    else 2 ** (attempt + 1)
                )
            except ValueError:
                delay = 2 ** (attempt + 1)

            delay = min(
                delay + random.uniform(0, 1),
                60
            )

            print(
                f"    Rate limited; retrying "
                f"in {delay:.1f}s"
            )

            time.sleep(delay)
            continue

        if response.status_code >= 500:
            if attempt == MAX_ATTEMPTS - 1:
                response.raise_for_status()

            time.sleep(
                min(2 ** (attempt + 1), 30)
            )
            continue

        response.raise_for_status()

        return response.json()

    raise RuntimeError(
        "Maximum retry attempts reached"
    )


# ============================================================
# AUTHENTICATION TEST
# ============================================================

def test_authentication(session):
    print("Testing OpenAlex authentication...")

    response = session.get(
        API_URL,
        params={
            "api_key": API_KEY,
            "search": "polynomial commitment",
            "per_page": 1
        },
        timeout=30
    )

    print("HTTP status:", response.status_code)

    if response.status_code != 200:
        print(
            "Server response:",
            response.text[:300]
        )

        raise SystemExit(
            "Authentication test failed. "
            "No discovery records were modified."
        )

    print("Authentication successful.\n")


# ============================================================
# MAIN DISCOVERY RECOVERY
# ============================================================

def main():

    # Resume from the recovered output if it exists.
    source = OUTPUT if OUTPUT.exists() else INPUT

    if not source.exists():
        raise FileNotFoundError(source)

    df = pd.read_csv(source).fillna("")

    required_columns = {
        "Title",
        "Year",
        "Discovery Status",
        "Error"
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    # Find only records with retryable errors.
    failed = (
        df["Discovery Status"].eq("ERROR")
        & df["Error"].astype(str).str.contains(
            RETRYABLE_ERRORS,
            case=False,
            regex=True
        )
    )

    positions = df.index[failed].tolist()

    print("Total records:", len(df))
    print("Unresolved errors to retry:", len(positions))
    print("Previously completed:", len(df) - len(positions))

    if not positions:
        print("No retryable records found.")
        return

    session = requests.Session()

    session.headers.update({
        "User-Agent": "PCS-Literature-Review/1.0",
        "Accept": "application/json"
    })

    # Do not touch saved results until authentication succeeds.
    test_authentication(session)

    for number, index in enumerate(
        positions,
        start=1
    ):
        title = str(df.at[index, "Title"])
        year = df.at[index, "Year"]

        print(
            f"\n[{number}/{len(positions)}] "
            f"{title}"
        )

        try:
            try:
                data = request_openalex(
                    session,
                    title
                )

            except ValueError as error:
                if "BAD_REQUEST_400" not in str(error):
                    raise

                clean_title = simplify_query(title)

                if clean_title == title:
                    raise

                print(
                    "    Retrying with simplified title:",
                    clean_title
                )

                data = request_openalex(
                    session,
                    clean_title
                )

            work = select_matching_work(
                data.get("results", []),
                title,
                year
            )

            # Clear stale results only after API success.
            for column in [
                "Error",
                "Matched Title",
                "OpenAlex ID",
                "DOI",
                "PDF Candidates",
                "Landing Pages",
                "Sources"
            ]:
                if column not in df.columns:
                    df[column] = ""

                df.at[index, column] = ""

            if work is None:
                df.at[
                    index, "Discovery Status"
                ] = "NO_MATCH"

            else:
                locations = extract_oa_locations(work)

                df.at[
                    index, "Matched Title"
                ] = work.get("title") or ""

                df.at[
                    index, "OpenAlex ID"
                ] = work.get("id") or ""

                df.at[
                    index, "DOI"
                ] = work.get("doi") or ""

                df.at[
                    index, "PDF Candidates"
                ] = " | ".join(
                    item["pdf"]
                    for item in locations
                    if item["pdf"]
                )

                df.at[
                    index, "Landing Pages"
                ] = " | ".join(
                    item["landing"]
                    for item in locations
                    if item["landing"]
                )

                df.at[
                    index, "Sources"
                ] = " | ".join(
                    item["source"]
                    for item in locations
                    if item["source"]
                )

                df.at[
                    index, "Discovery Status"
                ] = (
                    "OA_CANDIDATES"
                    if locations
                    else "NO_OA_LOCATION"
                )

            print(
                "  Status:",
                df.at[index, "Discovery Status"]
            )

        except Exception as error:
            message = str(error)

            df.at[index, "Discovery Status"] = "ERROR"
            df.at[index, "Error"] = message

            print("  Error:", message)

            # Stop the entire batch when credentials fail
            # or access is prohibited.
            if any(
                token in message
                for token in (
                    "AUTHENTICATION_FAILED",
                    "ACCESS_FORBIDDEN"
                )
            ):
                df.to_csv(OUTPUT, index=False)
                print(
                    "Stopping safely. "
                    "Checkpoint preserved."
                )
                break

        # Save after every paper.
        df.to_csv(OUTPUT, index=False)

        time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 55)
    print("UPDATED OPENALEX DISCOVERY SUMMARY")
    print("=" * 55)

    print(
        df["Discovery Status"].value_counts()
    )

    direct_pdf = df[
        df["PDF Candidates"].astype(str).str.strip() != ""
    ]

    print(
        "\nPapers with direct PDF candidates:",
        len(direct_pdf)
    )

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
