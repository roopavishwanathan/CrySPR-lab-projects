
import json
import re
import unicodedata
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from mlx_lm import load, generate


# =====================================================
# 1. CONFIGURATION
# =====================================================

MODEL = "mlx-community/gpt-oss-20b-MXFP4-Q8"

INPUT = "results/papers_with_abstracts.csv"
OUTPUT = "results/all_abstract_screening.csv"

Path("results").mkdir(parents=True, exist_ok=True)


# =====================================================
# 2. STRUCTURED OUTPUT SCHEMA
# =====================================================

class Evidence(BaseModel):
    quote: str


class PaperReview(BaseModel):
    classification: Literal[
        "NEW_PCS",
        "PCS_IMPROVEMENT",
        "NEW_RELATED_PRIMITIVE",
        "PCS_APPLICATION",
        "NOT_PCS",
        "UNCERTAIN"
    ]

    pcs_family: str | None = None
    technical_contributions: list[str]
    reasoning: str
    confidence: Literal["High", "Medium", "Low"]

    evidence: list[Evidence] = Field(
        default_factory=list,
        max_length=2
    )


# =====================================================
# 3. NORMALIZE EVIDENCE TEXT
# =====================================================

def normalize(text):
    text = unicodedata.normalize("NFKC", str(text))

    # Normalize quotation marks and hyphens.
    for char in ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]:
        text = text.replace(char, "-")

    for char in ["\u2018", "\u2019"]:
        text = text.replace(char, "'")

    for char in ["\u201c", "\u201d"]:
        text = text.replace(char, '"')

    # Normalize mathematical delimiters and spacing.
    text = text.replace("$", "")
    text = text.replace(r"\(", "").replace(r"\)", "")

    # Normalize simple LaTeX commands.
    text = re.sub(r"\\mathcal\{([A-Za-z])\}", r"\1", text)
    text = text.replace(r"\nu", "nu")
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)

    # Remove spacing differences.
    text = " ".join(text.split())

    return text.strip().strip('"“”\'')


# =====================================================
# 4. LOAD ALL PAPERS WITH ABSTRACTS
# =====================================================

df = pd.read_csv(INPUT).fillna("")

if df.empty:
    raise ValueError("The input CSV is empty.")

if "Title" not in df.columns:
    raise ValueError("Missing Title column.")

if "Abstract" not in df.columns:
    raise ValueError("Missing Abstract column.")

# Include ALL records with available abstracts.
papers = df[
    df["Abstract"].astype(str).str.strip() != ""
].copy()

print("=" * 65)
print("FULL PCS ABSTRACT SCREENING")
print("=" * 65)

print("Papers selected:", len(papers))


# =====================================================
# 5. CHECKPOINT RECOVERY
# =====================================================

if Path(OUTPUT).exists():

    previous = pd.read_csv(OUTPUT).fillna("")

    results = previous.to_dict("records")

    # Only skip records with a successful, valid
    # classification. Failed records remain retryable.
    completed = set()

    for _, row in previous.iterrows():

        if (
            str(row.get("Error", "")).strip() == ""
            and str(row.get("Review Status", "")) == "Preliminary"
        ):
            completed.add(str(row["Title"]))

    print(
        f"Previously completed: {len(completed)} papers."
    )

else:
    results = []
    completed = set()

pending = papers[
    ~papers["Title"].astype(str).isin(completed)
]

print("Pending papers:", len(pending))


# =====================================================
# 6. LOAD GPT-OSS ONLY IF NEEDED
# =====================================================

if len(pending) > 0:

    print("\nLoading OpenAI GPT-OSS 20B...")

    model, tokenizer = load(MODEL)

    print("Model loaded successfully.")

else:
    model = None
    tokenizer = None
    print("All papers have already been processed.")


# =====================================================
# 7. RESEARCH CLASSIFICATION PROMPT
# =====================================================

system_prompt = """
You are a cryptography research reviewer specializing
in polynomial commitment schemes (PCS).

Your task is to screen research papers for a systematic
literature survey of NEW polynomial commitment schemes.

You are given a PAPER TITLE and ABSTRACT.

Use ONLY the supplied abstract to determine the
authors' claimed technical contributions.

CLASSIFICATION CATEGORIES:

NEW_PCS:
Introduces a new polynomial commitment construction
that supports committing to polynomials and proving
polynomial evaluations.

This includes constructions based on pairings,
Reed-Solomon codes, FRI, lattices, inner-product
arguments, tensor codes, or other techniques.

PCS_IMPROVEMENT:
Improves an existing PCS without clearly introducing
a distinct commitment construction.

NEW_RELATED_PRIMITIVE:
Introduces a related primitive, such as list polynomial
commitments, polynomial IOPs, or specialized commitments,
whose relationship to conventional PCS requires review.

PCS_APPLICATION:
Uses an existing PCS inside a SNARK, STARK, blockchain
protocol, or another application without introducing
a new PCS.

NOT_PCS:
Does not substantively introduce or investigate
polynomial commitment constructions.

UNCERTAIN:
There is insufficient evidence in the abstract to
determine the technical contribution.

IMPORTANT RULES:

1. A new SNARK, STARK, IOP, or folding construction
   is not automatically a new PCS.

2. Do not classify a paper as NEW_PCS based only
   on its title.

3. Preserve borderline PCS papers for full-text review.

4. Do not invent technical properties or contributions.

5. Provide at most two SHORT, CONTINUOUS, VERBATIM
   quotations from the supplied ABSTRACT.

6. Do not omit words, insert ellipses, or paraphrase
   supporting quotations.

7. If no direct evidence is available, return
   an empty evidence array.

8. This is ABSTRACT-ONLY screening. All decisions
   are preliminary and require appropriate review.

9. Do not infer a new PCS merely because a paper
   uses polynomial commitments within a larger system.

RETURN ONLY A VALID JSON OBJECT:

{
  "classification": "NEW_PCS",
  "pcs_family": "code-based",
  "technical_contributions": [
    "Contribution 1",
    "Contribution 2"
  ],
  "reasoning": "Explanation based on the abstract",
  "confidence": "High",
  "evidence": [
    {
      "quote": "Exact quotation from the abstract"
    }
  ]
}
"""


# =====================================================
# 8. HELPER: EXTRACT GPT-OSS FINAL RESPONSE
# =====================================================

def extract_final_response(response):

    if "<|channel|>final<|message|>" in response:
        response = response.split(
            "<|channel|>final<|message|>"
        )[-1]

    response = response.split("<|end|>")[0]
    response = response.split("<|fim_suffix|>")[0]

    return response.strip()


# =====================================================
# 9. HELPER: SAVE CHECKPOINT
# =====================================================

def save_checkpoint(records):

    # Write to a temporary file first, then replace.
    # This protects the previous CSV if writing fails.
    temporary = OUTPUT + ".tmp"

    pd.DataFrame(records).to_csv(
        temporary,
        index=False
    )

    Path(temporary).replace(OUTPUT)


# =====================================================
# 10. BATCH CLASSIFICATION
# =====================================================

total = len(papers)

for position, (_, paper) in enumerate(
    papers.iterrows(),
    start=1
):

    title = str(paper["Title"])
    abstract = str(paper["Abstract"])

    if title in completed:
        print(
            f"[{position}/{total}] "
            f"Skipping completed: {title}"
        )
        continue

    print("\n" + "=" * 65)
    print(f"[{position}/{total}] {title}")
    print("=" * 65)

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": (
                f"PAPER TITLE:\n{title}\n\n"
                f"ABSTRACT:\n{abstract}\n\n"
                "Classify this paper using ONLY its abstract."
            )
        }
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    try:

        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1200,
            verbose=False
        )

        response = extract_final_response(response)

        match = re.search(
            r"\{.*\}",
            response,
            re.DOTALL
        )

        if not match:
            raise ValueError(
                "GPT-OSS returned no JSON object."
            )

        data = json.loads(match.group(0))

        review = PaperReview.model_validate(data)

        # Verify supporting quotations independently.
        evidence_checks = [
            bool(item.quote.strip())
            and normalize(item.quote) in normalize(abstract)
            for item in review.evidence
        ]

        all_evidence_verified = (
            bool(evidence_checks)
            and all(evidence_checks)
        )

        row = {
            "Title": title,
            "Conference": paper.get("Conference", ""),
            "Year": paper.get("Year", ""),

            "Classification": review.classification,
            "PCS Family": review.pcs_family or "unknown",

            "Technical Contributions": json.dumps(
                review.technical_contributions,
                ensure_ascii=False
            ),

            "Reasoning": review.reasoning,
            "Confidence": review.confidence,

            "Evidence": json.dumps(
                [item.quote for item in review.evidence],
                ensure_ascii=False
            ),

            "Evidence Checks": json.dumps(
                evidence_checks
            ),

            "Evidence Verified": all_evidence_verified,

            "Source": "Abstract only",
            "Review Status": "Preliminary",
            "Needs Full Text Review": True,

            "Error": ""
        }

    except (
        ValueError,
        ValidationError,
        RuntimeError,
        KeyError,
        TypeError
    ) as error:

        row = {
            "Title": title,
            "Conference": paper.get("Conference", ""),
            "Year": paper.get("Year", ""),

            "Classification": "UNCERTAIN",
            "PCS Family": "unknown",

            "Technical Contributions": "[]",
            "Reasoning": "",

            "Confidence": "Low",
            "Evidence": "[]",
            "Evidence Checks": "[]",
            "Evidence Verified": False,

            "Source": "Abstract only",
            "Review Status": "Needs review",
            "Needs Full Text Review": True,

            "Error": str(error)
        }

    # Remove an earlier failed attempt at the same paper
    # before storing a successful retry.
    results = [
        record for record in results
        if str(record["Title"]) != title
    ]

    results.append(row)

    save_checkpoint(results)

    print("Classification:", row["Classification"])
    print("PCS Family:", row["PCS Family"])
    print("Evidence Verified:", row["Evidence Verified"])

    if row["Error"]:
        print("Error:", row["Error"])


# =====================================================
# 11. FINAL SUMMARY
# =====================================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 65)
print("FULL ABSTRACT SCREENING SUMMARY")
print("=" * 65)

if results_df.empty:
    print("No results available.")
else:
    print("\nClassification counts:")
    print(
        results_df["Classification"].value_counts()
    )

    print(
        "\nEvidence verified:",
        int(results_df["Evidence Verified"].sum()),
        "/",
        len(results_df)
    )

    print(
        "\nSuccessfully processed:",
        int(
            (
                results_df["Review Status"]
                == "Preliminary"
            ).sum()
        ),
        "/",
        total
    )

print("\nOutput:", OUTPUT)
