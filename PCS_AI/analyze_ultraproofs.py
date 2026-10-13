
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from mlx_lm import load, generate


MODEL = "mlx-community/gpt-oss-20b-MXFP4-Q8"

SECTIONS = Path(
    "papers/extracted/UltraProofs_sections.txt"
)

CONTRIBUTIONS = Path(
    "papers/extracted/UltraProofs_contributions.txt"
)

OUTPUT = Path(
    "results/UltraProofs_fulltext_review.json"
)


class Contribution(BaseModel):
    construction_name: str

    authors_claim: str

    evidence_quote: str

    classification: Literal[
        "NEW_PCS",
        "PCS_IMPROVEMENT",
        "NEW_RELATED_PRIMITIVE",
        "PCS_APPLICATION",
        "NOT_PCS",
        "UNCERTAIN"
    ]

    pcs_family: str

    technical_interpretation: str

    evidence_verified: bool = False


class PaperAnalysis(BaseModel):
    paper_title: str
    source: str
    contributions: list[Contribution] = Field(
        default_factory=list
    )


system_prompt = """
You are a cryptography researcher evaluating the
novelty of polynomial commitment schemes.

The input contains the paper's abstract, introduction,
and authors' stated contributions.

Identify distinct technical contributions separately.

For each contribution:

1. Identify the construction name.

2. Describe what the AUTHORS explicitly claim.

3. Provide one short, exact, contiguous quotation
   from the CONTRIBUTIONS text.

4. Classify the contribution using these categories:

NEW_PCS:
A new polynomial commitment construction that allows
committing to a polynomial and proving evaluations.

PCS_IMPROVEMENT:
A modification of an existing PCS without a clearly
distinct construction.

NEW_RELATED_PRIMITIVE:
A new related primitive, such as an RS code commitment,
vector commitment, or specialized commitment mechanism.

PCS_APPLICATION:
An application using existing PCS constructions.

NOT_PCS:
A contribution unrelated to polynomial commitments.

UNCERTAIN:
Insufficient information to determine novelty.

5. Identify the PCS family, where applicable.

6. Explain the technical reasoning separately from
   the authors' actual claims.

Never infer PCS novelty solely from a paper title.

Do not treat an RS code commitment as automatically
equivalent to a polynomial commitment scheme.

Do not fabricate quotations.

Return only valid JSON.

Avoid LaTeX backslashes in the JSON output.

Use the following structure:

{
  "paper_title": "UltraProofs: Scalable Reed-Solomon Code Commitment",
  "source": "Abstract + Introduction + Contributions",
  "contributions": [
    {
      "construction_name": "Name",
      "authors_claim": "Authors' stated claim",
      "evidence_quote": "Exact substring from the contributions text",
      "classification": "NEW_PCS",
      "pcs_family": "code-based",
      "technical_interpretation": "Reasoning"
    }
  ]
}
"""


def extract_json(response):
    if "<|channel|>final<|message|>" in response:
        response = response.split(
            "<|channel|>final<|message|>"
        )[-1]

    response = response.split("<|fim_suffix|>")[0]
    response = response.split("<|end|>")[0]

    response = response.strip()

    return json.loads(response)


def main():
    sections = SECTIONS.read_text(encoding="utf-8")
    contributions_text = CONTRIBUTIONS.read_text(
        encoding="utf-8"
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": (
                "ABSTRACT AND INTRODUCTION:\n"
                f"{sections}\n\n"
                "AUTHORS' CONTRIBUTIONS:\n"
                f"{contributions_text}\n\n"
                "Analyze each distinct contribution."
            )
        }
    ]

    print("Loading GPT-OSS 20B...")
    model, tokenizer = load(MODEL)

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    print("Analyzing UltraProofs...")

    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=2200,
        verbose=False
    )

    # Preserve the raw response for debugging.
    raw_path = OUTPUT.with_suffix(".raw.txt")
    raw_path.write_text(response, encoding="utf-8")

    data = extract_json(response)
    analysis = PaperAnalysis.model_validate(data)

    # Verify exact source quotations.
    for item in analysis.contributions:
        item.evidence_verified = (
            bool(item.evidence_quote.strip())
            and item.evidence_quote in contributions_text
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        analysis.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print("\nFULL-TEXT REVIEW")
    print("=" * 60)

    for item in analysis.contributions:
        print("\nConstruction:", item.construction_name)
        print("Classification:", item.classification)
        print("Evidence verified:", item.evidence_verified)
        print("Authors' claim:", item.authors_claim)
        print("Technical interpretation:",
              item.technical_interpretation)

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
