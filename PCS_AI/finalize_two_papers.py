
import json
import pandas as pd

INPUT = "results/all_abstract_screening_final_evidence.csv"
ABSTRACTS = "results/papers_with_abstracts.csv"
OUTPUT = "results/all_abstract_screening_complete.csv"

df = pd.read_csv(INPUT).fillna("")
source = pd.read_csv(ABSTRACTS).fillna("")

abstract_lookup = dict(
    zip(source["Title"], source["Abstract"])
)

corrections = {
    "SNARKBlock: Federated Anonymous Blocklisting from Hidden Common Input Aggregate Proofs": {
        "classification": "NOT_PCS",
        "family": "Not applicable",
        "contributions": [
            "Introduces SNARKBlock for federated anonymous blocklisting.",
            "Introduces HICIAP for aggregating Groth16 proofs sharing a hidden input."
        ],
        "reasoning": (
            "The abstract introduces a proof aggregation system "
            "and an anonymous blocklisting protocol, rather than "
            "a new polynomial commitment scheme."
        ),
        "quotes": [
            "Our core technical advance, of separate interest, is the HICIAP zero-knowledge proof system",
            "HICIAP resolves this problem by aggregating n Groth16 proofs into one"
        ]
    },

    "Secure Lookup Tables: Faster, Leaner, and More General": {
        "classification": "NOT_PCS",
        "family": "Not applicable",
        "contributions": [
            "Introduces MARLUT, a generalized secure lookup-table protocol.",
            "Introduces distributed zero-knowledge proofs for inner-product relations over rings."
        ],
        "reasoning": (
            "The abstract describes a secure lookup-table protocol "
            "and distributed zero-knowledge proofs. It does not "
            "claim to introduce a polynomial commitment scheme."
        ),
        "quotes": [
            "we present MARLUT, a new generalized and optimized LUT construction",
            "designing a new distributed zero-knowledge proof for inner-product relations"
        ]
    }
}

df["Classification Review Method"] = df.get(
    "Classification Review Method", ""
)

corrected = 0

for title, update in corrections.items():

    matches = df.index[df["Title"] == title]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one result for {title}"
        )

    abstract = str(abstract_lookup.get(title, ""))

    checks = [
        quote in abstract
        for quote in update["quotes"]
    ]

    if not all(checks):
        raise ValueError(
            f"Source evidence mismatch for {title}: {checks}"
        )

    idx = matches[0]

    # Preserve previous model output.
    if "Original Classification" not in df.columns:
        df["Original Classification"] = ""

    if "Original Reasoning" not in df.columns:
        df["Original Reasoning"] = ""

    df.at[idx, "Original Classification"] = df.at[
        idx, "Classification"
    ]
    df.at[idx, "Original Reasoning"] = df.at[
        idx, "Reasoning"
    ]

    df.at[idx, "Classification"] = update["classification"]
    df.at[idx, "PCS Family"] = update["family"]
    df.at[idx, "Technical Contributions"] = json.dumps(
        update["contributions"], ensure_ascii=False
    )
    df.at[idx, "Reasoning"] = update["reasoning"]
    df.at[idx, "Confidence"] = "High"

    df.at[idx, "Original Evidence"] = df.at[idx, "Evidence"]
    df.at[idx, "Evidence"] = json.dumps(
        update["quotes"], ensure_ascii=False
    )
    df.at[idx, "Evidence Checks"] = json.dumps(checks)
    df.at[idx, "Evidence Verified"] = True
    df.at[idx, "Evidence Status"] = "VERIFIED"
    df.at[idx, "Evidence Correction"] = "Exact abstract quotations"

    df.at[idx, "Review Status"] = "Preliminary"
    df.at[idx, "Needs Full Text Review"] = True
    df.at[idx, "Error"] = ""
    df.at[idx, "Classification Review Method"] = (
        "Assistant-assisted abstract review"
    )

    corrected += 1

df.to_csv(OUTPUT, index=False)

print("=" * 60)
print("FINAL SCREENING SUMMARY")
print("=" * 60)

print("Papers corrected:", corrected)
print("Total records:", len(df))
print("\nEvidence statuses:")
print(df["Evidence Status"].value_counts())
print("\nClassification counts:")
print(df["Classification"].value_counts())
print("\nOutput:", OUTPUT)
