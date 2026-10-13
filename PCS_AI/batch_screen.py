
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
OUTPUT = "results/all_abstract_screening_final_evidence.csv"

MAX_TOKENS = 1800
MAX_ATTEMPTS = 3

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
# 3. EVIDENCE NORMALIZATION
# =====================================================

def normalize(text):
    text = unicodedata.normalize("NFKC", str(text))

    for char in [
        "\u2010", "\u2011", "\u2012",
        "\u2013", "\u2014", "\u2212"
    ]:
        text = text.replace(char, "-")

    for char in ["\u2018", "\u2019"]:
        text = text.replace(char, "'")

    for char in ["\u201c", "\u201d"]:
        text = text.replace(char, '"')

    text = text.replace("$", "")
    text = text.replace(r"\(", "").replace(r"\)", "")

    text = re.sub(
        r"\\mathcal\{([A-Za-z])\}",
        r"\1",
        text
    )

    text = text.replace(r"\nu", "nu")
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)

    return " ".join(text.split()).strip('"“”\'')


# =====================================================
# 4. LOAD ABSTRACT DATASET
# =====================================================

papers = pd.read_csv(INPUT).fillna("")

required_columns = {"Title", "Abstract"}

missing = required_columns - set(papers.columns)

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

papers = papers[
    papers["Abstract"].astype(str).str.strip() != ""
].copy()

if papers.empty:
    raise ValueError("No abstracts found.")

print("=" * 65)
print("PCS ABSTRACT SCREENING - ERROR RECOVERY")
print("=" * 65)

print("Total papers:", len(papers))


# =====================================================
# 5. LOAD EXISTING RESULTS
# =====================================================

if Path(OUTPUT).exists():

    previous = pd.read_csv(OUTPUT).fillna("")

    # Preserve any manual evidence corrections.
    results = previous.to_dict("records")

    completed = set()

    for _, row in previous.iterrows():

        if (
            str(row.get("Error", "")).strip() == ""
            and str(row.get("Review Status", "")) == "Preliminary"
        ):
            completed.add(str(row["Title"]))

else:
    results = []
    completed = set()


pending = papers[
    ~papers["Title"].astype(str).isin(completed)
].copy()

print("Already completed:", len(completed))
print("Pending:", len(pending))

for title in pending["Title"]:
    print(" -", title)


# =====================================================
# 6. SYSTEM PROMPT
# =====================================================

system_prompt = """
You are a cryptography research reviewer specializing
in polynomial commitment schemes (PCS).

You are screening research papers for a systematic
literature review of new polynomial commitment schemes.

Use ONLY the supplied title and abstract.

CLASSIFICATIONS:

NEW_PCS:
Introduces a genuinely new polynomial commitment
construction supporting polynomial commitments
and evaluation proofs.

PCS_IMPROVEMENT:
Improves an existing polynomial commitment scheme
without clearly introducing a distinct construction.

NEW_RELATED_PRIMITIVE:
Introduces a related primitive, such as a vector
commitment, list polynomial commitment, polynomial
interactive oracle proof, or specialized commitment,
whose relationship to conventional PCS requires review.

PCS_APPLICATION:
Uses an existing polynomial commitment scheme
without introducing a new PCS construction.

NOT_PCS:
Does not substantively introduce or investigate
polynomial commitments.

UNCERTAIN:
The supplied abstract is insufficient to determine
the technical contribution.

RESEARCH RULES:

1. A new SNARK, STARK, folding scheme, IOP, or
   vector commitment is not automatically a new PCS.

2. Do not infer PCS novelty from the paper title.

3. Preserve borderline candidates for full-text review.

4. Do not invent contributions or technical properties.

5. The technical_contributions field must contain
   your interpretations of the abstract, not fabricated
   statements attributed to the authors.

6. Provide at most two short, contiguous, verbatim
   supporting quotations from the abstract.

7. If the abstract does not contain suitable supporting
   quotations, return an empty evidence list.

8. Treat every classification as preliminary.

JSON RULES:

Return exactly one valid JSON object.

Use double quotes for JSON strings.

Escape every backslash correctly.

Do not output LaTeX commands inside JSON strings.

For mathematical notation, use simple plain text,
for example O(N), FRI, or KZG.

Do not use Markdown code fences.

Do not include explanations outside the JSON.

Required structure:

{
  "classification": "NEW_PCS",
  "pcs_family": "code-based",
  "technical_contributions": [
    "Description of contribution"
  ],
  "reasoning": "Explanation grounded in the abstract",
  "confidence": "High",
  "evidence": [
    {
      "quote": "Exact continuous substring from the abstract"
    }
  ]
}
"""


# =====================================================
# 7. LOAD GPT-OSS
# =====================================================

if not pending.empty:

    print("\nLoading GPT-OSS 20B...")

    model, tokenizer = load(MODEL)

    print("Model loaded successfully.")

else:
    model = None
    tokenizer = None


# =====================================================
# 8. EXTRACT AND PARSE JSON
# =====================================================

def parse_model_response(response):

    if "<|channel|>final<|message|>" in response:
        response = response.split(
            "<|channel|>final<|message|>"
        )[-1]

    response = response.split("<|fim_suffix|>")[0]
    response = response.split("<|end|>")[0]
    response = response.strip()

    # First try parsing the entire response.
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Then extract the first well-delimited JSON object.
    decoder = json.JSONDecoder()

    for match in re.finditer(r"\{", response):

        try:
            data, _ = decoder.raw_decode(
                response[match.start():]
            )

            if isinstance(data, dict):
                return data

        except json.JSONDecodeError:
            continue

    raise ValueError(
        "Could not parse a valid JSON object from GPT-OSS."
    )


# =====================================================
# 9. SAVE CHECKPOINT ATOMICALLY
# =====================================================

def save_checkpoint(records):

    temporary = Path(OUTPUT + ".tmp")

    pd.DataFrame(records).to_csv(
        temporary,
        index=False
    )

    temporary.replace(OUTPUT)


# =====================================================
# 10. CLASSIFY ONE PAPER
# =====================================================

def classify_paper(title, abstract):

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
                "Return the required JSON classification."
            )
        }
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:

            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=MAX_TOKENS,
                verbose=False
            )

            data = parse_model_response(response)

            review = PaperReview.model_validate(data)

            return review

        except (
            ValueError,
            ValidationError,
            RuntimeError,
            TypeError,
            KeyError
        ) as error:

            last_error = error

            print(
                f"Attempt {attempt}/{MAX_ATTEMPTS} "
                f"failed: {error}"
            )

    raise RuntimeError(
        f"All attempts failed: {last_error}"
    )


# =====================================================
# 11. PROCESS PENDING PAPERS
# =====================================================

total = len(papers)

for position, (_, paper) in enumerate(
    papers.iterrows(),
    start=1
):

    title = str(paper["Title"])
    abstract = str(paper["Abstract"])

    if title in completed:
        continue

    print("\n" + "=" * 65)
    print(f"[{position}/{total}] {title}")
    print("=" * 65)

    try:

        review = classify_paper(title, abstract)

        checks = [
            bool(item.quote.strip())
            and normalize(item.quote) in normalize(abstract)
            for item in review.evidence
        ]

        verified = bool(checks) and all(checks)

        if not review.evidence:
            evidence_status = "NO_EVIDENCE"
        elif verified:
            evidence_status = "VERIFIED"
        else:
            evidence_status = "QUOTE_MISMATCH"

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

            "Evidence Checks": json.dumps(checks),
            "Evidence Verified": verified,
            "Evidence Status": evidence_status,

            "Source": "Abstract only",
            "Review Status": "Preliminary",
            "Needs Full Text Review": True,

            "Error": "",

            # Preserve schema introduced during
            # manual evidence correction.
            "Original Evidence": "",
            "Evidence Correction": ""
        }

    except Exception as error:

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
            "Evidence Status": "PROCESSING_ERROR",

            "Source": "Abstract only",
            "Review Status": "Needs review",
            "Needs Full Text Review": True,

            "Error": str(error),

            "Original Evidence": "",
            "Evidence Correction": ""
        }

    # Replace only the record belonging to this title.
    results = [
        record for record in results
        if str(record["Title"]) != title
    ]

    results.append(row)

    save_checkpoint(results)

    print("Classification:", row["Classification"])
    print("Evidence Status:", row["Evidence Status"])

    if row["Error"]:
        print("Error:", row["Error"])


# =====================================================
# 12. FINAL SUMMARY
# =====================================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 65)
print("FINAL PCS SCREENING SUMMARY")
print("=" * 65)

if results_df.empty:
    print("No results found.")

else:
    print("\nClassifications:")
    print(
        results_df["Classification"].value_counts()
    )

    print("\nEvidence statuses:")
    print(
        results_df["Evidence Status"].value_counts(
            dropna=False
        )
    )

    print("\nProcessing errors:")
    print(
        results_df[
            results_df["Error"].astype(str).str.strip() != ""
        ][["Title", "Error"]]
    )

    print("\nTotal records:", len(results_df))

print("\nResults saved to:", OUTPUT)
