
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


INPUT = "results/all_abstract_screening.csv"
ABSTRACTS = "results/papers_with_abstracts.csv"
OUTPUT = "results/all_abstract_screening_revalidated.csv"


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text))

    for char in ["\u2010", "\u2011", "\u2012",
                 "\u2013", "\u2014", "\u2212"]:
        text = text.replace(char, "-")

    for char in ["\u2018", "\u2019"]:
        text = text.replace(char, "'")

    for char in ["\u201c", "\u201d"]:
        text = text.replace(char, '"')

    text = text.replace("$", "")
    text = text.replace(r"\(", "").replace(r"\)", "")

    text = re.sub(r"\\mathcal\{([A-Za-z])\}", r"\1", text)
    text = text.replace(r"\nu", "nu")
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)

    text = " ".join(text.split())

    return text.strip().strip('"“”\'')


results = pd.read_csv(INPUT).fillna("")
abstracts = pd.read_csv(ABSTRACTS).fillna("")

# Match by title, preserving the input row order.
abstract_lookup = dict(
    zip(abstracts["Title"].astype(str),
        abstracts["Abstract"].astype(str))
)

original_verified = (
    results["Evidence Verified"]
    .astype(str)
    .str.lower()
    .eq("true")
    .sum()
)

new_checks = []
new_verified = []
statuses = []

for _, row in results.iterrows():
    title = str(row["Title"])
    abstract = abstract_lookup.get(title, "")

    if str(row["Error"]).strip():
        checks = []
        status = "PROCESSING_ERROR"

    elif not abstract:
        checks = []
        status = "ABSTRACT_MISSING"

    else:
        try:
            quotes = json.loads(row["Evidence"])
            if not isinstance(quotes, list):
                raise ValueError("Evidence must be a list")

            checks = [
                bool(str(q).strip())
                and normalize(q) in normalize(abstract)
                for q in quotes
            ]

            if not quotes:
                status = "NO_EVIDENCE"
            elif all(checks):
                status = "VERIFIED"
            else:
                status = "QUOTE_MISMATCH"

        except (ValueError, TypeError):
            checks = []
            status = "INVALID_EVIDENCE"

    verified = status == "VERIFIED"

    new_checks.append(json.dumps(checks))
    new_verified.append(verified)
    statuses.append(status)


results["Evidence Checks"] = new_checks
results["Evidence Verified"] = new_verified
results["Evidence Status"] = statuses

Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT, index=False)

print("=" * 60)
print("EVIDENCE REVALIDATION SUMMARY")
print("=" * 60)

print("Total papers:", len(results))
print("Previously verified:", int(original_verified))
print("Currently verified:", sum(new_verified))
print("\nEvidence statuses:")
print(results["Evidence Status"].value_counts())

print("\nOutput:", OUTPUT)
