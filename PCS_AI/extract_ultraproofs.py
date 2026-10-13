
import fitz
from pathlib import Path

PDF = Path(
    "papers/pdfs/UltraProofs_Scalable_Reed-Solomon_Code_Commitment.pdf"
)

OUTPUT = Path("papers/extracted/UltraProofs_fulltext.txt")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)

with OUTPUT.open("w", encoding="utf-8") as out:
    for page_number, page in enumerate(doc, start=1):
        out.write(f"\n{'=' * 70}\n")
        out.write(f"PDF PAGE {page_number}\n")
        out.write(f"{'=' * 70}\n\n")

        # Extract left-column text before right-column text.
        blocks = [
            b for b in page.get_text("blocks")
            if len(b) >= 5 and isinstance(b[4], str)
        ]

        mid = page.rect.width / 2

        left = [b for b in blocks if b[0] < mid]
        right = [b for b in blocks if b[0] >= mid]

        left.sort(key=lambda b: (b[1], b[0]))
        right.sort(key=lambda b: (b[1], b[0]))

        for block in left + right:
            out.write(block[4].strip() + "\n\n")

doc.close()

print("Extraction complete.")
print("Saved:", OUTPUT)