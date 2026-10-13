import pandas as pd
from mlx_lm import load, generate
import fitz

# Load our dataset
df = pd.read_csv("pcs_merged_review.csv").fillna("")

# Select first paper
paper = df[
    df["Title"].str.contains("RedShift", case=False, na=False)
].iloc[0]

title = paper["Title"]
abstract = paper["Abstract"]
print("Title:", title)
print("Abstract:", abstract[:500])



# with fitz.open("DeepFold.pdf") as doc:
#     page = doc[1]
#     abstract = page.get_text("text", sort=True)

# Load Qwen 2.5 locally
print("Loading Qwen 2.5 14B...")

model, tokenizer = load(
    "mlx-community/Qwen2.5-14B-Instruct-4bit"
)

system_prompt = """
You are an expert reviewer of cryptographic polynomial
commitment schemes (PCS).

Analyze ONLY the provided abstract.

Classify the paper into exactly one category:

NEW_PCS:
Introduces a new polynomial commitment scheme supporting
polynomial commitments and evaluation proofs.

PCS_IMPROVEMENT:
Improves an existing polynomial commitment scheme without
introducing a distinct construction.

NEW_RELATED_PCS_PRIMITIVE:
Introduces a new related primitive, such as list polynomial
commitments, whose relationship to a conventional PCS
requires further examination.

PCS_APPLICATION:
Uses an existing polynomial commitment scheme in a
larger protocol without proposing a new PCS.

NOT_PCS:
Does not introduce or substantively study polynomial
commitment constructions.

UNCERTAIN:
The abstract does not provide sufficient evidence.

Important:
A new SNARK, STARK, IOP, or folding scheme is not
automatically a new PCS.

Do not infer technical properties that are not explicitly
supported by the abstract.

Respond using this format:

Classification: <one category>

Evidence: <an exact quotation from the abstract>

Reason: <brief technical explanation>
"""

messages = [
    {"role": "system", "content": system_prompt},
    {
        "role": "user",
        "content": f"Title: {title}\n\nAbstract:\n{abstract}"
    }
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

print("\nAnalyzing:", title)

response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=300,
    verbose=False
)

print("\nQWEN CLASSIFICATION:\n")
print(response)
