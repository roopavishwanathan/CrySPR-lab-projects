
import re
import shutil
import hashlib
import unicodedata
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd
import pymupdf


ROOT = Path.home() / "PCS_AI"
INVENTORY = ROOT / "results/pdf_acquisition_all_196.csv"
OUTPUT = ROOT / "papers/pdfs"
LOG = ROOT / "results/final_arxiv_registration_log.csv"

DOWNLOAD_FOLDERS = [
    Path.home() / "Downloads",
    ROOT / "downloads",
]

EXCLUDED_TITLES = [
    "Polynomial Commitments for Galois Rings",
    "E2Easy: a Simple Lattice-Based in-Person",
]

OUTPUT.mkdir(parents=True, exist_ok=True)


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = text.replace("\u00ad", "")
    text = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    return " ".join(text.split())


def similarity(a, b):
    return SequenceMatcher(
        None, normalize(a), normalize(b)
    ).ratio()


def title_score(title, text):
    expected = normalize(title)
    extracted = normalize(text)

    if expected in extracted:
        return 1.0

    words = extracted.split()
    count = len(expected.split())

    if count == 0 or len(words) < count:
        return 0.0

    return max(
        (
            similarity(
                expected,
                " ".join(words[i:i + count])
            )
            for i in range(
                min(len(words) - count + 1, 1000)
            )
        ),
        default=0.0
    )


def safe_filename(title):
    stem = re.sub(
        r"[^A-Za-z0-9]+", "_", title
    ).strip("_")[:75]

    digest = hashlib.sha256(
        title.encode("utf-8")
    ).hexdigest()[:8]

    return stem + "_" + digest + ".pdf"


def main():
    df = pd.read_csv(INVENTORY).fillna("")

    if len(df) != 196:
        raise ValueError("Unexpected inventory size.")

    missing = df[df["Status"] != "DOWNLOADED"].copy()

    if len(missing) != 12:
        raise ValueError(
            f"Expected 12 remaining records, found {len(missing)}."
        )

    excluded_indices = []

    for _, row in missing.iterrows():
        if any(
            phrase.lower() in str(row["Title"]).lower()
            for phrase in EXCLUDED_TITLES
        ):
            excluded_indices.append(row.name)

    if len(excluded_indices) != 2:
        raise ValueError(
            "Expected exactly two excluded papers."
        )

    targets = missing.drop(excluded_indices)

    if len(targets) != 10:
        raise ValueError(
            f"Expected 10 target papers, found {len(targets)}."
        )

    print("ArXiv papers expected:", len(targets))
    print("Papers to exclude:", len(excluded_indices))

    files = []

    for folder in DOWNLOAD_FOLDERS:
        if folder.exists():
            files.extend(folder.glob("*.pdf"))
            files.extend(folder.glob("*.PDF"))

    files = sorted(set(files))

    print("PDFs found in download folders:", len(files))

    # Only files with a matching title will be registered.
    candidates = []

    for path in files:
        try:
            with pymupdf.open(path) as doc:
                if doc.page_count == 0:
                    continue

                pages = doc.page_count
                text = " ".join(
                    doc[i].get_text("text")
                    for i in range(min(3, pages))
                )

            scores = sorted(
                [
                    (
                        title_score(row["Title"], text),
                        index
                    )
                    for index, row in targets.iterrows()
                ],
                reverse=True
            )

            best_score, best_index = scores[0]
            second_score = (
                scores[1][0] if len(scores) > 1 else 0
            )

            if best_score >= 0.90 and (
                best_score - second_score >= 0.04
            ):
                candidates.append({
                    "Path": path,
                    "Index": best_index,
                    "Score": best_score,
                    "Pages": pages
                })

        except Exception as error:
            print("Skipping unreadable file:", path.name)
            print("Reason:", error)

    # Resolve multiple candidate PDFs for the same title.
    grouped = {}

    for item in candidates:
        grouped.setdefault(item["Index"], []).append(item)

    selected = {}

    for index, matches in grouped.items():
        if len(matches) == 1:
            selected[index] = matches[0]
        else:
            print(
                "\nMultiple matching PDFs for:",
                df.at[index, "Title"]
            )
            for match in matches:
                print(
                    " ",
                    match["Path"].name,
                    round(match["Score"], 4)
                )
            print("Skipped pending manual selection.")

    print("\nUnique verified matches:", len(selected))

    if selected:
        backup = INVENTORY.with_name(
            INVENTORY.stem
            + "_backup_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".csv"
        )

        shutil.copy2(INVENTORY, backup)
        print("Backup:", backup)
    else:
        backup = None

    logs = []
    registered = 0

    for index, item in selected.items():
        title = str(df.at[index, "Title"])
        source = item["Path"]
        destination = OUTPUT / safe_filename(title)

        print("\nRegistering:", title)
        print("Source:", source.name)

        if destination.exists():
            print("Destination already exists; skipped.")
            logs.append({
                "Title": title,
                "Source": str(source),
                "Status": "DESTINATION_EXISTS"
            })
            continue

        shutil.copy2(source, destination)

        df.at[index, "Status"] = "DOWNLOADED"
        df.at[index, "Local PDF"] = str(destination)
        df.at[index, "PDF Identity"] = "TITLE_MATCH"
        df.at[index, "Pages"] = item["Pages"]
        df.at[index, "Acquisition Source"] = (
            "arXiv browser download"
        )
        df.at[index, "Acquisition URL"] = (
            "arXiv browser download; URL not recorded"
        )

        df.to_csv(INVENTORY, index=False)

        logs.append({
            "Title": title,
            "Source": str(source),
            "Destination": str(destination),
            "Score": round(item["Score"], 4),
            "Status": "REGISTERED"
        })

        registered += 1

    # Explicitly exclude the two user-selected records.
    for index in excluded_indices:
        if df.at[index, "Status"] != "DOWNLOADED":
            df.at[index, "Status"] = "EXCLUDED_USER_REQUEST"
            df.at[index, "Local PDF"] = ""

    df.to_csv(INVENTORY, index=False)
    pd.DataFrame(logs).to_csv(LOG, index=False)

    acquired = df["Status"].eq("DOWNLOADED").sum()
    excluded = df["Status"].eq(
        "EXCLUDED_USER_REQUEST"
    ).sum()
    pending = len(df) - acquired - excluded

    print("\n" + "=" * 55)
    print("FINAL ARXIV REGISTRATION SUMMARY")
    print("=" * 55)

    print("Newly registered:", registered)
    print("Total PDFs acquired:", acquired)
    print("Excluded by user:", excluded)
    print("Remaining included papers:", pending)
    print("Total records:", len(df))

    if pending:
        print("\nStill missing:")
        for title in df.loc[
            ~df["Status"].isin([
                "DOWNLOADED",
                "EXCLUDED_USER_REQUEST"
            ]),
            "Title"
        ]:
            print(" -", title)

    print("\nLog:", LOG)


if __name__ == "__main__":
    main()
