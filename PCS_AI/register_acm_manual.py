
import re
import shutil
import unicodedata
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd
import pymupdf


INVENTORY = Path("results/pdf_acquisition_all_196.csv")
CHECKLIST = Path("results/acm_download_checklist.csv")

INPUT_DIR = Path("papers/acm_manual")
OUTPUT_DIR = Path("papers/pdfs")
LOG = Path("results/acm_manual_registration_log.csv")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text))
    text = text.casefold()
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def title_score(expected, pdf_text):
    expected = normalize(expected)
    actual = normalize(pdf_text)

    if expected in actual:
        return 1.0

    words = actual.split()
    count = len(expected.split())

    return max(
        (
            SequenceMatcher(
                None,
                expected,
                " ".join(words[i:i + count])
            ).ratio()
            for i in range(
                max(0, len(words) - count + 1)
            )
        ),
        default=0.0
    )


def main():
    inventory = pd.read_csv(INVENTORY).fillna("")
    checklist = pd.read_csv(CHECKLIST).fillna("")

    files = sorted(INPUT_DIR.glob("*.pdf"))

    print("ACM PDFs found:", len(files))

    if not files:
        print("No PDFs found. Check:", INPUT_DIR)
        return

    backup = INVENTORY.with_name(
        INVENTORY.stem
        + "_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".csv"
    )

    shutil.copy2(INVENTORY, backup)

    logs = []
    registered = 0
    used_titles = set()

    for pdf in files:
        print(f"\nProcessing: {pdf.name}")

        record = {
            "Original File": pdf.name,
            "Matched Title": "",
            "Score": "",
            "Status": "",
            "Destination": "",
            "Error": ""
        }

        try:
            with pymupdf.open(pdf) as doc:
                pages = doc.page_count

                if pages < 1:
                    raise ValueError("Empty PDF")

                text = " ".join(
                    doc[i].get_text("text")
                    for i in range(min(2, pages))
                )

            scores = []

            for _, paper in checklist.iterrows():
                score = title_score(
                    paper["Title"], text
                )
                scores.append((score, paper))

            scores.sort(
                key=lambda item: item[0],
                reverse=True
            )

            best_score, best = scores[0]

            title = str(best["Title"])

            record["Matched Title"] = title
            record["Score"] = round(best_score, 4)

            print("  Matched:", title)
            print("  Confidence:", round(best_score, 4))

            if best_score < 0.93:
                record["Status"] = "REVIEW_REQUIRED"
                print("  Insufficient title match.")
                logs.append(record)
                continue

            if title in used_titles:
                record["Status"] = "DUPLICATE_IN_BATCH"
                logs.append(record)
                continue

            used_titles.add(title)

            match = (
                inventory["Title"].map(normalize)
                == normalize(title)
            ) & (
                inventory["Conference"].isin(
                    ["ACM CCS", "ACM ASIACCS"]
                )
            )

            if match.sum() != 1:
                record["Status"] = "INVENTORY_MATCH_ERROR"
                logs.append(record)
                continue

            index = inventory.index[match][0]

            if inventory.at[index, "Status"] == "DOWNLOADED":
                record["Status"] = "ALREADY_REGISTERED"
                logs.append(record)
                print("  Already registered.")
                continue

            destination = (
                OUTPUT_DIR / str(best["Save As"])
            )

            if destination.exists():
                record["Status"] = "DESTINATION_EXISTS"
                logs.append(record)
                continue

            shutil.copy2(pdf, destination)

            inventory.at[index, "Status"] = "DOWNLOADED"
            inventory.at[index, "Local PDF"] = str(destination)
            inventory.at[index, "PDF Identity"] = "TITLE_MATCH"
            inventory.at[index, "Pages"] = pages
            inventory.at[index, "Acquisition Source"] = (
                "ACM browser download"
            )
            inventory.at[index, "Acquisition URL"] = (
                str(best["ACM Link"])
            )

            inventory.to_csv(INVENTORY, index=False)

            record["Status"] = "REGISTERED"
            record["Destination"] = str(destination)

            registered += 1

            print("  Registered:", pages, "pages")

        except Exception as error:
            record["Status"] = "ERROR"
            record["Error"] = str(error)
            print("  ERROR:", error)

        logs.append(record)
        pd.DataFrame(logs).to_csv(LOG, index=False)

    print("\n" + "=" * 55)
    print("ACM MANUAL PDF REGISTRATION SUMMARY")
    print("=" * 55)

    if logs:
        print(
            pd.DataFrame(logs)["Status"]
            .value_counts()
        )

    acquired = inventory["Status"].eq("DOWNLOADED").sum()

    remaining_acm = (
        inventory["Conference"].isin(
            ["ACM CCS", "ACM ASIACCS"]
        )
        & inventory["Status"].ne("DOWNLOADED")
    ).sum()

    print("\nNewly registered:", registered)
    print("Total PDFs acquired:", acquired)
    print("Remaining overall:", len(inventory) - acquired)
    print("Remaining ACM papers:", remaining_acm)
    print("Backup:", backup)
    print("Log:", LOG)


if __name__ == "__main__":
    main()
