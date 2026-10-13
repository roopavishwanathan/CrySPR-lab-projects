import pymupdf
import re

pdf_path = "DeepFold.pdf"
output_path = "DeepFold_sections.txt"

def extract_two_columns(page):
    blocks = page.get_text("blocks")
    midpoint = page.rect.width / 2

    left = []
    right = []

    for block in blocks:
        x0, y0, x1, y1, text, *_ = block

        if not text.strip():
            continue

        if x0 < midpoint:
            left.append((y0, text))
        else:
            right.append((y0, text))

    left.sort(key=lambda x: x[0])
    right.sort(key=lambda x: x[0])

    return (
        "".join(t for _, t in left)
        + "\n"
        + "".join(t for _, t in right)
    )

sections = []

with pymupdf.open(pdf_path) as doc:
    for page_index in [1, 2, 3]:
        text = extract_two_columns(doc[page_index])

        # Remove line-break hyphenation.
        text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

        sections.append(
            f"\n========== PDF PAGE {page_index + 1} ==========\n"
            + text
        )

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sections))

print("Saved:", output_path)
print("Total characters:", sum(len(s) for s in sections))