
import json
import pandas as pd

INPUT = "results/all_abstract_screening_corrected.csv"
ABSTRACTS = "results/papers_with_abstracts.csv"
OUTPUT = "results/all_abstract_screening_final_evidence.csv"

df = pd.read_csv(INPUT).fillna("")
source = pd.read_csv(ABSTRACTS).fillna("")

abstract_lookup = dict(
    zip(source["Title"], source["Abstract"])
)

# All quotations below are exact substrings of the
# supplied original abstracts.
corrections = {
    "EPID with Efficient Proof of Non-Revocation": [
        "we reconsider this problem by proposing a new EPID system with a much more efficient proof of non-revocation.",
        "The latter is no longer zero-knowledge but its combination with the other components of the EPID system still results in an anonymous signature."
    ],

    "Scalable Time-Lock Puzzle": [
        "we present a scalable TLP designed for real-world scenarios involving a large number of puzzles",
        "ED-TLP is the first protocol of its kind."
    ],

    "Reconstructing Chameleon Hash: Full Security and the Multi-Party Setting": [
        "we propose the first CH scheme, which supports full security",
        "we investigate the security of CH in the multi-party setting"
    ],

    "Conan: Distributed Proofs of Compliance for Anonymous Data Collection": [
        "Our main contribution is a novel anonymous, compliant data collection protocol that realizes the above goal.",
        "each client's communication and computation overhead do not grow with respect to the number of clients n."
    ],

    "Hekaton: Horizontally-Scalable zkSNARKs Via Proof Aggregation": [
        "we introduce Hekaton, a zkSNARK that overcomes these barriers and can efficiently handle arbitrarily large computations.",
        "We construct Hekaton via a new ''distribute-and-aggregate'' framework"
    ],

    "Lite-PoT: Practical Powers-of-Tau Setup Ceremony": [
        "a fraud-proof protocol to reduce the number of expensive on-chain cryptographic group operations to O(1) per contributor.",
        "a proof aggregation technique that batches m randomness contributions into one on-chain update with only O(d) on-chain operations"
    ],

    "PriDe CT: Towards Public Consensus, Private Transactions, and Forward Secrecy in Decentralized Payments": [
        "PriDe CT uses linear homomor-phic encryption as Anonymous Zether but with simpler zero-knowledge proofs.",
        "PriDeFUL CT uses an updatable public key encryption scheme to achieve forward secrecy by introducing a new DDH-based construction in the standard model."
    ],

    "MicroNova: Folding-Based Arguments with Efficient (On-Chain) Verification": [
        "MicroNova requires a universal trusted setup and can employ any existing setup material created for the popular KZG univariate polynomial commitment scheme.",
        "the compressed proof consists of O(log N) group elements"
    ],

    "zkLoRA: Fine-Tuning Large Language Models with Verifiable Security via Zero-Knowledge Proofs": [
        "VeriLoRA employs advanced cryptographic techniques -- such as lookup arguments, sumcheck protocols, and polynomial commitments --",
        "The framework provides end-to-end verifiability for forward propagation, backward propagation, and parameter updates during LoRA fine-tuning"
    ],

    "Accelerating the Delfs-Galbraith Algorithm with Fast Subfield Root Detection": [
        "We give a new algorithm for ﬁnding an isogeny",
        "Our core ingredi-ent is a novel method of rapidly determining whether a polynomial"
    ]
}

if "Original Evidence" not in df.columns:
    df["Original Evidence"] = df["Evidence"]

if "Evidence Correction" not in df.columns:
    df["Evidence Correction"] = ""

corrected = 0

for idx, row in df.iterrows():

    if row["Evidence Status"] != "QUOTE_MISMATCH":
        continue

    title = row["Title"]

    if title not in corrections:
        continue

    abstract = str(abstract_lookup.get(title, ""))
    quotes = corrections[title]

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

print("=" * 60)
print("FINAL EVIDENCE CORRECTION SUMMARY")
print("=" * 60)

print("Papers corrected:", corrected)
print("\nEvidence statuses:")
print(df["Evidence Status"].value_counts())
print("\nOutput:", OUTPUT)
