
import json
import pandas as pd

INPUT = "results/all_abstract_screening_revalidated.csv"
ABSTRACTS = "results/papers_with_abstracts.csv"
OUTPUT = "results/all_abstract_screening_corrected.csv"

df = pd.read_csv(INPUT).fillna("")
source = pd.read_csv(ABSTRACTS).fillna("")

abstract_lookup = dict(zip(source["Title"], source["Abstract"]))

# Exact source substrings. These phrases are deliberately
# short to avoid punctuation and mathematical formatting issues.
corrections = {
    "Short Privacy-Preserving Proofs of Liabilities": [
        "This paper introduces a fully privacy-preserving PoL scheme with short proofs.",
        "We store the prover's liabilities in a novel data structure, the sparse summation Verkle tree (SSVT)"
    ],
    "Private Access Control for Function Secret Sharing": [
        "In this paper, we initiate the study of access control for FSS.",
        "The main building block behind our efficiency improvement is a discrete-logarithm zero-knowledge proof-of-knowledge over secret-shared elements"
    ],
    "ALPACA: Anonymous Blocklisting with Constant-Sized Updatable Proofs": [
        "In this work, we introduce ALPACA, the first anonymous blocklisting system",
        "Our key technique is a new variant of incrementally verifiable computation (IVC), designed to ensure anonymity."
    ],
    "HyperPianist: Pianist with Linear-Time Prover and Logarithmic Communication Cost": [
        "we design a distributed multivariate polynomial interactive oracle proof (PIOP) system",
        "we adapt two additively-homomorphic multivariate polynomial commitment schemes"
    ],
    "ZKSL: Verifiable and Efficient Split Federated Learning via Asynchronous Zero-Knowledge Proofs": [
        "we present ZKSL, an efficient and asynchronous VFL framework",
        "Privacy-Commitment PLONK (PC-PLONK), a lightweight extension that supports low-cost, iteration-by-iteration parameter commitments"
    ]
}

df["Original Evidence"] = df["Evidence"]
df["Evidence Correction"] = ""

corrected = 0

for idx, row in df.iterrows():
    title = row["Title"]

    if title not in corrections:
        continue

    abstract = str(abstract_lookup.get(title, ""))
    quotes = corrections[title]

    # Require every proposed quotation to exist in
    # the original abstract exactly as written.
    checks = [quote in abstract for quote in quotes]

    if not all(checks):
        print("NOT CORRECTED:", title, checks)
        continue

    df.at[idx, "Evidence"] = json.dumps(
        quotes, ensure_ascii=False
    )
    df.at[idx, "Evidence Checks"] = json.dumps(checks)
    df.at[idx, "Evidence Verified"] = True
    df.at[idx, "Evidence Status"] = "VERIFIED"
    df.at[idx, "Evidence Correction"] = "Exact source quotations"

    corrected += 1

df.to_csv(OUTPUT, index=False)

print("Papers corrected:", corrected)
print("Remaining mismatches:",
      (df["Evidence Status"] == "QUOTE_MISMATCH").sum())
print("Saved:", OUTPUT)
