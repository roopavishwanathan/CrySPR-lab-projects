import pymupdf

with pymupdf.open("DeepFold.pdf") as doc:
    page = doc[1]

    blocks = page.get_text("blocks")

    # Sort primarily by column, then vertical position
    page_width = page.rect.width

    left = []
    right = []

    for block in blocks:
        x0, y0, x1, y1, text, *_ = block

        if not text.strip():
            continue

        if x0 < page_width / 2:
            left.append((y0, text))
        else:
            right.append((y0, text))

    left.sort(key=lambda item: item[0])
    right.sort(key=lambda item: item[0])

    print("========== LEFT COLUMN ==========")

    for _, text in left:
        print(text)

    print("\n========== RIGHT COLUMN ==========")

    for _, text in right:
        print(text)
    with open("DeepFold_extracted.txt", "w", encoding="utf-8") as f:
        f.write("".join(text for _, text in left))
        f.write("\n\n")
        f.write("".join(text for _, text in right))

print("\nSaved extracted text to DeepFold_extracted.txt")