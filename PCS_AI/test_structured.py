
import json
import re
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from mlx_lm import load, generate

MODEL = "mlx-community/gpt-oss-20b-MXFP4-Q8"

# Define the expected classification structure.
class Evidence(BaseModel):
    quote: str
    pdf_page: int

class PaperReview(BaseModel):
    classification: Literal[
        "NEW_PCS",
        "PCS_IMPROVEMENT",
        "NEW_RELATED_PRIMITIVE",
        "PCS_APPLICATION",
        "NOT_PCS",
        "UNCERTAIN"
    ]
    pcs_family: str
    technical_contributions: list[str]
    reasoning: str
    confidence: Literal["High", "Medium", "Low"]
    evidence: list[Evidence] = Field(max_length=2)

# Load the previously extracted paper sections.
with open("DeepFold_sections.txt", encoding="utf-8") as f:
    paper_text = f.read()

model, tokenizer = load(MODEL)

system_prompt = """
You are a cryptography literature-review assistant.

Determine whether the authors introduce a new polynomial
commitment scheme (PCS), improve an existing PCS,
introduce a related primitive, or merely use a PCS.

A new SNARK, STARK, or IOP is not automatically a new PCS.

Use only the provided text.
Provide at most two short, verbatim evidence quotations.
Every quotation must be continuous, without ellipses.
Use the PDF PAGE markers for page numbers.

Return ONLY a valid JSON object with these fields:
classification, pcs_family, technical_contributions,
reasoning, confidence, evidence.

Allowed classifications:
NEW_PCS, PCS_IMPROVEMENT, NEW_RELATED_PRIMITIVE,
PCS_APPLICATION, NOT_PCS, UNCERTAIN.

confidence must be High, Medium, or Low.

evidence must be an array of objects, each containing:
quote (string) and pdf_page (integer).

Do not use Markdown code fences.
"""

messages = [
    {"role": "system", "content": system_prompt},
    {
        "role": "user",
        "content": (
            "Classify this paper:\n\n" + paper_text
        )
    }
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=1200,
    verbose=False
)

# Keep only the model's final answer.
if "<|channel|>final<|message|>" in response:
    response = response.split(
        "<|channel|>final<|message|>"
    )[-1]

response = response.split("<|end|>")[0].strip()

print("\nRAW MODEL RESPONSE:\n")
print(response)

# Extract and validate the JSON.
try:
    match = re.search(r"\{.*\}", response, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found.")

    data = json.loads(match.group(0))
    review = PaperReview.model_validate(data)

    print("\nVALIDATED RESULT:\n")
    print(review.model_dump_json(indent=2))

except (ValueError, ValidationError) as error:
    print("\nVALIDATION FAILED:")
    print(error)
import unicodedata

def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u2011", "-")
    text = text.replace("\u2010", "-")
    text = text.replace("\u2013", "-")
    text = " ".join(text.split())
    return text

print("\n========== EVIDENCE VERIFICATION ==========")

# Split extracted text using the PDF page markers.
page_sections = re.split(
    r"========== PDF PAGE (\d+) ==========",
    paper_text
)

pages = {}

for i in range(1, len(page_sections), 2):
    page_number = int(page_sections[i])
    pages[page_number] = page_sections[i + 1]

for i, item in enumerate(review.evidence, start=1):
    quote = normalize(item.quote)
    page_text = normalize(pages.get(item.pdf_page, ""))

    verified = bool(quote) and quote in page_text

    print(f"\nEvidence {i}:")
    print("PDF page:", item.pdf_page)
    print("Verified:", verified)
    print("Quote:", item.quote)