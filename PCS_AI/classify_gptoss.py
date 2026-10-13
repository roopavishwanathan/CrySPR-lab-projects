
import re
import pandas as pd
from mlx_lm import load, generate

# ==========================================
# 1. CONFIGURATION
# ==========================================

MODEL_NAME = "mlx-community/gpt-oss-20b-MXFP4-Q8"

CSV_PATH = "pcs_merged_review.csv"
TEXT_PATH = "DeepFold_sections.txt"

# ==========================================
# 2. LOAD PUBLICATION DATASET
# ==========================================

df = pd.read_csv(CSV_PATH).fillna("")

papers = df[
    df["Title"].str.contains(
        "DeepFold",
        case=False,
        na=False
    )
]

if papers.empty:
    raise ValueError("DeepFold not found in the CSV.")

paper = papers.iloc[0]

title = paper["Title"]

print("=" * 60)
print("SELECTED PAPER")
print("=" * 60)

print("Title:", title)
print("Conference:", paper["Conference"])
print("Year:", paper["Year"])

# ==========================================
# 3. LOAD EXTRACTED PAPER TEXT
# ==========================================

with open(TEXT_PATH, "r", encoding="utf-8") as f:
    paper_text = f.read()

if not paper_text.strip():
    raise ValueError(
        "DeepFold_sections.txt is empty."
    )

print("\nSource: DeepFold.pdf")
print("Pages: PDF pages 2-4")
print("Extracted characters:", len(paper_text))

print("\nText preview:\n")
print(paper_text[:700])

# ==========================================
# 4. LOAD OPENAI GPT-OSS 20B
# ==========================================

print("\nLoading OpenAI GPT-OSS 20B...")

model, tokenizer = load(MODEL_NAME)

print("Model loaded successfully.")

# ==========================================
# 5. RESEARCH SCREENING INSTRUCTIONS
# ==========================================

system_prompt = """
You are an expert cryptography research-paper reviewer
specializing in polynomial commitment schemes (PCS).

Your task is to determine whether the supplied research
paper introduces a NEW polynomial commitment scheme.

Analyze the ABSTRACT, INTRODUCTION, and CONTRIBUTIONS
in the supplied text.

Use ONLY the supplied text as evidence.

A polynomial commitment scheme enables a prover to
commit to a polynomial and subsequently prove claimed
polynomial evaluations.

CLASSIFICATION CATEGORIES

NEW_PCS:
The authors introduce a new polynomial commitment
construction that supports commitments and evaluation
proofs. New constructions may be based on pairings,
lattices, error-correcting codes, inner-product arguments,
or other cryptographic techniques.

PCS_IMPROVEMENT:
The authors improve or optimize an existing PCS without
introducing a distinct polynomial commitment construction.

NEW_RELATED_PRIMITIVE:
The paper introduces a new related primitive such as a
list polynomial commitment, polynomial IOP, or specialized
commitment primitive, whose relationship to a conventional
PCS requires closer technical examination.

PCS_APPLICATION:
The authors use an existing PCS within a SNARK, STARK,
blockchain protocol, or another application without
introducing a new PCS.

NOT_PCS:
The publication does not substantively propose or
investigate polynomial commitment constructions.

UNCERTAIN:
The supplied evidence is insufficient to determine
whether a new PCS is proposed.

IMPORTANT SCREENING RULES

1. Introducing a new SNARK, STARK, IOP, or proof system
   does NOT automatically imply introducing a new PCS.

2. A new PCS may be presented as a building block
   within a larger proof system.

3. Distinguish a new PCS construction from an
   optimization of an existing PCS.

4. Identify the exact technical contribution claimed
   by the authors.
5. Provide at most TWO supporting evidence quotations.
   Each quotation must be a short, continuous, verbatim
   excerpt copied from the supplied paper text.

6. Do not use ellipses (...) or combine sentences
   from different locations into one quotation.

7. For each quotation, identify the PDF page number
   using the page markers in the supplied text.

8. Prefer evidence from the Contributions section.

9. If no exact supporting passage exists, state
   "No direct evidence found" and classify as UNCERTAIN.

REQUIRED OUTPUT FORMAT

Classification: <one category>

PCS Family: <pairing-based / code-based / lattice-based /
inner-product-based / other / unknown>

Evidence:
<exact quotation from the supplied text>

Technical Contributions:
<brief explanation of the claimed PCS contributions>

Reason:
<why the paper belongs to this category>

Confidence:
<High / Medium / Low>
"""

# ==========================================
# 6. PREPARE INPUT FOR GPT-OSS
# ==========================================

messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "user",
        "content": (
            f"RESEARCH PAPER TITLE:\n{title}\n\n"
            f"SOURCE: DeepFold.pdf, PDF pages 2-4\n\n"
            f"PAPER TEXT:\n{paper_text}\n\n"
            "Classify this paper based only on the "
            "supplied evidence."
        )
    }
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# ==========================================
# 7. RUN GPT-OSS CLASSIFICATION
# ==========================================

print("\nAnalyzing paper with GPT-OSS...\n")

response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=1000,
    verbose=False
)

# ==========================================
# 8. EXTRACT FINAL ANSWER
# ==========================================

# GPT-OSS sometimes includes reasoning-channel
# text. Keep only the final response.

if "<|channel|>final<|message|>" in response:
    response = response.split(
        "<|channel|>final<|message|>"
    )[-1]

response = response.split("<|end|>")[0]
response = response.split("<|fim_suffix|>")[0]
response = response.strip()

# ==========================================
# 9. DISPLAY CLASSIFICATION
# ==========================================

print("\n" + "=" * 60)
print("GPT-OSS PAPER CLASSIFICATION")
print("=" * 60)

print("Title:", title)
print("Source: DeepFold.pdf, PDF pages 2-4")
print()
print(response)

# ==========================================
# 10. VERIFY QUOTED EVIDENCE
# ==========================================

def normalize_text(text):
    """
    Normalize whitespace and quotation marks
    for checking quotations.

    This is not a semantic similarity check.
    """
    text = text.replace("\u2011", "-")
    text = text.replace("\u2010", "-")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")

    return re.sub(r"\s+", " ", text).strip()


# Identify double-quoted excerpts.
quoted_passages = re.findall(
    r'["“]([^"”]+)["”]',
    response
)

normalized_source = normalize_text(paper_text)

print("\n" + "=" * 60)
print("EVIDENCE VERIFICATION")
print("=" * 60)

if not quoted_passages:
    print("No quoted passages detected.")
    print("Manual evidence verification required.")

else:
    for index, quote in enumerate(
        quoted_passages,
        start=1
    ):
        normalized_quote = normalize_text(quote)

        verified = (
            normalized_quote in normalized_source
        )

        print(f"\nEvidence {index}:")
        print("Quotation:", quote)
        print("Exact normalized match:", verified)

        if not verified:
            print(
                "WARNING: Quotation not found verbatim. "
                "Manual verification required."
            )

# ==========================================
# 11. SAVE RESULT
# ==========================================

output_path = "DeepFold_gptoss_result.txt"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("Paper: " + title + "\n")
    f.write("Source: DeepFold.pdf, PDF pages 2-4\n\n")
    f.write(response + "\n")

print("\nResult saved to:", output_path)
