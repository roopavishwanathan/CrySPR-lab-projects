#!/usr/bin/env python3

import requests
import json
import time
import re
import os
from collections import Counter

# ============================================================
# USER SETTINGS
# ============================================================

# ----- Core cross-chain terms -----

CROSS_CHAIN_TERMS = [
    '"cross-chain bridge"',
    '"cross-chain bridges"',
    '"blockchain bridge"',
    '"blockchain bridges"',
    '"cross-chain bridging"',
    '"blockchain bridging"',
    '"cross-chain protocol"',
    '"cross-chain protocols"',
    '"cross-chain interoperability"',
    '"blockchain interoperability"',
    '"cross-chain transaction"',
    '"cross-chain transactions"',
    '"cross-chain communication"',
    '"cross-chain transfer"',
    '"cross-chain transfers"',
]


# ----- CUSTOM KEYWORDS -----
#
# Edit these however you want.
#
# Each family becomes a separate Semantic Scholar query.

CUSTOM_KEYWORDS = {

    "general_security": [
        "attack",
        "attacks",
        "exploit",
        "exploits",
        "vulnerability",
        "vulnerabilities",
        "hack",
        "security",
        "threat",
        "malicious",
        "adversarial",
        "compromise",
        "defense",
        "detection",
    ],

    "contract_logic": [
        "reentrancy",
        '"access control"',
        '"business logic"',
        '"integer error"',
        '"arithmetic error"',
        '"race condition"',
        '"unsafe external call"',
        '"contract upgrade"',
    ],

    "forgery_and_message_validation": [
        '"fake deposit"',
        '"fake burn"',
        '"forged event"',
        '"event forgery"',
        '"log forgery"',
        '"message forgery"',
        '"proof forgery"',
        '"invalid proof"',
        '"message validation"',
    ],

    "authentication_and_trust": [
        '"oracle manipulation"',
        '"custodian manipulation"',
        '"key compromise"',
        '"private key leakage"',
        '"private key theft"',
        '"validator compromise"',
        '"validator equivocation"',
        '"validator misbehavior"',
        '"relayer attack"',
        '"light-client verification"',
        '"light client verification"',
    ],

    "consensus_replay_and_finality": [
        "replay",
        '"replay attack"',
        "finality",
        '"delayed finality"',
        '"chain reorganization"',
        '"double spending"',
        '"timestamp manipulation"',
        '"consensus failure"',
        '"51% attack"',
    ],

    "economic_and_liquidity": [
        '"liquidity attack"',
        '"liquidity exhaustion"',
        '"liquidity manipulation"',
        '"economic attack"',
        '"fee manipulation"',
        '"sandwich attack"',
        '"front running"',
        "MEV",
    ],

    "availability_and_frontend": [
        '"denial of service"',
        "DoS",
        "availability",
        '"frontend attack"',
        '"front-end attack"',
        '"RPC attack"',
        '"endpoint attack"',
    ],
}


# ============================================================
# SEARCH SETTINGS
# ============================================================

YEAR_START = 2021
YEAR_END = 2026

OUTPUT_FILE = "custom_cross_chain_search.json"
CHECKPOINT_FILE = "custom_cross_chain_checkpoint.json"

API_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

FIELDS = ",".join([
    "paperId",
    "title",
    "abstract",
    "year",
    "venue",
    "publicationVenue",
    "publicationDate",
    "authors",
    "externalIds",
    "url",
    "citationCount",
])

# Delay between successful requests.
REQUEST_DELAY = 2.0

# Retry configuration.
MAX_RETRIES = 8
INITIAL_BACKOFF = 5


# ============================================================
# HELPERS
# ============================================================

def normalize_title(title):
    title = str(title or "").lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return " ".join(title.split())


def build_query(keywords):

    cross_chain = " | ".join(CROSS_CHAIN_TERMS)
    attack_terms = " | ".join(keywords)

    return f"({cross_chain}) + ({attack_terms})"


def request_with_retry(params):

    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = requests.get(
                API_URL,
                params=params,
                timeout=60,
            )

            print(
                f"Attempt {attempt} | "
                f"Status {response.status_code}"
            )

            if response.status_code == 200:
                return response

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = backoff

                else:
                    wait = backoff

                print(
                    f"Rate limited. Waiting "
                    f"{wait:.1f} seconds..."
                )

                time.sleep(wait)

                backoff = min(backoff * 2, 120)

                continue

            if response.status_code in {
                500, 502, 503, 504
            }:

                print(
                    f"Server error. Waiting "
                    f"{backoff} seconds..."
                )

                time.sleep(backoff)

                backoff = min(backoff * 2, 120)

                continue

            print(response.text[:1000])

            return None

        except requests.RequestException as e:

            print(
                f"Request error: {e}"
            )

            print(
                f"Waiting {backoff} seconds..."
            )

            time.sleep(backoff)

            backoff = min(backoff * 2, 120)

    return None


# ============================================================
# SEARCH ONE FAMILY
# ============================================================

def search_family(family, keywords):

    query = build_query(keywords)

    print("\n" + "=" * 100)
    print(f"SEARCHING: {family}")
    print("=" * 100)

    print("\nQUERY:")
    print(query)
    print()

    papers = []

    token = None

    page = 0

    while True:

        page += 1

        params = {
            "query": query,
            "fields": FIELDS,
            "year": f"{YEAR_START}-{YEAR_END}",
        }

        if token:
            params["token"] = token

        response = request_with_retry(params)

        if response is None:

            print(
                f"Stopping family {family} "
                "because request failed."
            )

            break

        payload = response.json()

        batch = payload.get("data", [])

        print(
            f"Page {page} | "
            f"Received {len(batch)} papers"
        )

        for paper in batch:

            paper["_matched_family"] = family
            paper["_matched_query"] = query

            papers.append(paper)

        token = payload.get("token")

        if not token:
            break

        time.sleep(REQUEST_DELAY)

    print(
        f"\n{family}: {len(papers)} raw papers"
    )

    return papers


# ============================================================
# MERGE DUPLICATES
# ============================================================

def deduplicate(papers):

    unique = {}

    for paper in papers:

        paper_id = paper.get("paperId")

        title_key = normalize_title(
            paper.get("title")
        )

        key = paper_id or title_key

        if not key:
            continue

        family = paper.get(
            "_matched_family"
        )

        query = paper.get(
            "_matched_query"
        )

        if key not in unique:

            clean = dict(paper)

            clean["matched_families"] = (
                [family] if family else []
            )

            clean["matched_queries"] = (
                [query] if query else []
            )

            unique[key] = clean

        else:

            existing = unique[key]

            if (
                family
                and family not in
                existing["matched_families"]
            ):
                existing[
                    "matched_families"
                ].append(family)

            if (
                query
                and query not in
                existing["matched_queries"]
            ):
                existing[
                    "matched_queries"
                ].append(query)

    return list(unique.values())


# ============================================================
# CHECKPOINT
# ============================================================

def save_checkpoint(results):

    with open(
        CHECKPOINT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Checkpoint saved: "
        f"{CHECKPOINT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 100)
    print("CUSTOM CROSS-CHAIN PAPER SEARCH")
    print("=" * 100)

    print(
        f"Years: {YEAR_START}-{YEAR_END}"
    )

    print(
        f"Keyword families: "
        f"{len(CUSTOM_KEYWORDS)}"
    )

    print()

    for family in CUSTOM_KEYWORDS:

        print(
            f" - {family}: "
            f"{len(CUSTOM_KEYWORDS[family])} "
            "keywords"
        )

    all_results = []

    completed = []

    # --------------------------------------------------------
    # Resume from checkpoint if one exists
    # --------------------------------------------------------

    if os.path.exists(CHECKPOINT_FILE):

        print(
            "\nExisting checkpoint found."
        )

        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            checkpoint = json.load(f)

        all_results = checkpoint.get(
            "papers",
            []
        )

        completed = checkpoint.get(
            "completed_families",
            []
        )

        print(
            "Completed families:",
            completed
        )

        print(
            "Recovered raw papers:",
            len(all_results)
        )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    for family, keywords in CUSTOM_KEYWORDS.items():

        if family in completed:

            print(
                f"\nSkipping completed family: "
                f"{family}"
            )

            continue

        papers = search_family(
            family,
            keywords,
        )

        all_results.extend(papers)

        completed.append(family)

        save_checkpoint({
            "completed_families": completed,
            "papers": all_results,
        })

        time.sleep(REQUEST_DELAY)

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique = deduplicate(
        all_results
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    unique.sort(
        key=lambda p: (
            int(p.get("year") or 0),
            normalize_title(
                p.get("title")
            ),
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            unique,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 100)
    print("SEARCH COMPLETE")
    print("=" * 100)

    print(
        "Raw records:",
        len(all_results)
    )

    print(
        "Unique papers:",
        len(unique)
    )

    print(
        "Saved:",
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # YEAR DISTRIBUTION
    # --------------------------------------------------------

    years = Counter(
        p.get("year")
        for p in unique
    )

    print("\nBY YEAR")

    for year in sorted(
        years,
        key=lambda x: int(x or 0)
    ):

        print(
            f"{year}: {years[year]}"
        )

    # --------------------------------------------------------
    # FAMILY DISTRIBUTION
    # --------------------------------------------------------

    families = Counter()

    for p in unique:

        for family in p.get(
            "matched_families",
            []
        ):
            families[family] += 1

    print("\nBY QUERY FAMILY")

    for family, count in (
        families.most_common()
    ):

        print(
            f"{family:40} {count}"
        )

    # --------------------------------------------------------
    # TITLES
    # --------------------------------------------------------

    print("\n" + "=" * 100)
    print("TITLES")
    print("=" * 100)

    for i, p in enumerate(
        unique,
        1,
    ):

        families_string = ", ".join(
            p.get(
                "matched_families",
                []
            )
        )

        print(
            f"{i:4}. "
            f"{p.get('title')} "
            f"| {p.get('year')} "
            f"| {p.get('venue')} "
            f"| {families_string}"
        )


if __name__ == "__main__":
    main()