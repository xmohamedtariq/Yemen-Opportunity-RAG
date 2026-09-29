from pathlib import Path
import time

import pandas as pd

from fetch_sources import (
    fetch_source,
    RAW_DIR,
    METADATA_DIR,
)


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

SOURCES_FILE = ROOT / "sources.csv"
PROCESSED_DIR = ROOT / "data" / "processed"

REPORT_FILE = (
    METADATA_DIR / "refetch_report.csv"
)


# ---------------------------------------------------------
# Sources that need to be downloaded again
# ---------------------------------------------------------

TARGET_IDS = [
       "OPP-021",

]


# ---------------------------------------------------------
# Remove old/stale files
# ---------------------------------------------------------

def remove_old_files(source_id):
    """
    Remove old files for a source before downloading
    the updated version.

    This prevents stale content from remaining in the
    dataset if a new fetch fails.
    """

    possible_raw_files = [
        RAW_DIR / f"{source_id}.html",
        RAW_DIR / f"{source_id}.htm",
        RAW_DIR / f"{source_id}.pdf",
    ]

    for file_path in possible_raw_files:
        if file_path.exists():
            file_path.unlink()

            print(
                f"[REMOVED OLD] "
                f"{file_path.name}"
            )

    processed_file = (
        PROCESSED_DIR
        / f"{source_id}.txt"
    )

    if processed_file.exists():
        processed_file.unlink()

        print(
            f"[REMOVED OLD] "
            f"{processed_file.name}"
        )

    metadata_file = (
        METADATA_DIR
        / f"{source_id}.json"
    )

    if metadata_file.exists():
        metadata_file.unlink()

        print(
            f"[REMOVED OLD] "
            f"{metadata_file.name}"
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    # -----------------------------------------------------
    # Check sources.csv
    # -----------------------------------------------------

    if not SOURCES_FILE.exists():
        print(
            f"[ERROR] sources.csv not found: "
            f"{SOURCES_FILE}"
        )
        return

    sources = pd.read_csv(
        SOURCES_FILE
    )

    required_columns = {
        "source_id",
        "title",
        "url",
    }

    missing_columns = (
        required_columns
        - set(sources.columns)
    )

    if missing_columns:
        print(
            "[ERROR] Missing required "
            "columns in sources.csv:"
        )

        for column in sorted(
            missing_columns
        ):
            print(
                f" - {column}"
            )

        return

    # -----------------------------------------------------
    # Normalize source IDs
    # -----------------------------------------------------

    sources["source_id"] = (
        sources["source_id"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # Select only target sources
    # -----------------------------------------------------

    selected = sources[
        sources["source_id"].isin(
            TARGET_IDS
        )
    ].copy()

    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Selective Source Re-fetch")
    print("=" * 60)
    print()

    print(
        f"Target sources: "
        f"{len(TARGET_IDS)}"
    )

    print(
        f"Found in sources.csv: "
        f"{len(selected)}"
    )

    print()

    # -----------------------------------------------------
    # Confirm all target IDs exist
    # -----------------------------------------------------

    found_ids = set(
        selected["source_id"]
        .tolist()
    )

    missing_ids = [
        source_id
        for source_id in TARGET_IDS
        if source_id not in found_ids
    ]

    if missing_ids:
        print(
            "[ERROR] Some target source IDs "
            "are missing from sources.csv:"
        )

        for source_id in missing_ids:
            print(
                f" - {source_id}"
            )

        return

    # -----------------------------------------------------
    # Check duplicates
    # -----------------------------------------------------

    duplicate_ids = (
        sources[
            sources["source_id"].duplicated(
                keep=False
            )
        ]["source_id"]
        .unique()
        .tolist()
    )

    if duplicate_ids:
        print(
            "[ERROR] Duplicate source IDs "
            "found in sources.csv:"
        )

        for source_id in duplicate_ids:
            print(
                f" - {source_id}"
            )

        return

    # -----------------------------------------------------
    # Preserve TARGET_IDS order
    # -----------------------------------------------------

    selected = (
        selected
        .set_index("source_id")
        .loc[TARGET_IDS]
        .reset_index()
    )

    results = []

    # -----------------------------------------------------
    # Fetch each selected source
    # -----------------------------------------------------

    for _, source in selected.iterrows():

        source_id = str(
            source["source_id"]
        ).strip()

        print()
        print("=" * 60)

        remove_old_files(
            source_id
        )

        result = fetch_source(
            source
        )

        results.append(
            result
        )

        print("=" * 60)

        # Small delay between websites
        time.sleep(0.5)

    # -----------------------------------------------------
    # Build report
    # -----------------------------------------------------

    report = pd.DataFrame(
        results
    )

    report.to_csv(
        REPORT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    successful = (
        report["status"]
        == "success"
    ).sum()

    failed = (
        report["status"]
        == "failed"
    ).sum()

    html_files = (
        report["file"]
        .fillna("")
        .str.endswith(".html")
    ).sum()

    pdf_files = (
        report["file"]
        .fillna("")
        .str.endswith(".pdf")
    ).sum()

    # -----------------------------------------------------
    # Final summary
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("Selective re-fetch finished")
    print("=" * 60)

    print(
        f"Target sources: "
        f"{len(report)}"
    )

    print(
        f"Successful: "
        f"{successful}"
    )

    print(
        f"Failed: "
        f"{failed}"
    )

    print(
        f"HTML files: "
        f"{html_files}"
    )

    print(
        f"PDF files: "
        f"{pdf_files}"
    )

    print()

    print(
        f"Report saved to: "
        f"{REPORT_FILE}"
    )

    # -----------------------------------------------------
    # Show failed IDs
    # -----------------------------------------------------

    if failed:

        print()
        print(
            "Failed source IDs:"
        )

        failed_rows = report[
            report["status"]
            == "failed"
        ]

        for _, row in (
            failed_rows.iterrows()
        ):
            print(
                f" - {row['source_id']}"
            )

    else:
        print()
        print(
            "[SUCCESS] All target sources "
            "were downloaded successfully."
        )


if __name__ == "__main__":
    main()