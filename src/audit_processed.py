from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"
METADATA_DIR = ROOT / "data" / "metadata"

REPORT_FILE = METADATA_DIR / "processed_quality_report.csv"


SUSPICIOUS_PHRASES = [
    "access denied",
    "forbidden",
    "enable javascript",
    "javascript is required",
    "checking your browser",
    "verify you are human",
    "captcha",
    "page not found",
    "404 not found",
    "service unavailable",
]


def inspect_file(text_file: Path):
    source_id = text_file.stem

    text = text_file.read_text(
        encoding="utf-8",
        errors="ignore",
    ).strip()

    metadata_file = (
        METADATA_DIR / f"{source_id}.json"
    )

    metadata = {}

    if metadata_file.exists():
        metadata = json.loads(
            metadata_file.read_text(
                encoding="utf-8"
            )
        )

    char_count = len(text)
    word_count = len(text.split())

    text_lower = text.lower()

    found_phrases = [
        phrase
        for phrase in SUSPICIOUS_PHRASES
        if phrase in text_lower
    ]

    issues = []

    if char_count < 500:
        issues.append("very_short")

    elif char_count < 1000:
        issues.append("short")

    if found_phrases:
        issues.append(
            "suspicious_page:"
            + "|".join(found_phrases)
        )

    status = (
        "review"
        if issues
        else "good"
    )

    return {
        "source_id": source_id,
        "title": metadata.get(
            "title", ""
        ),
        "provider": metadata.get(
            "provider", ""
        ),
        "category": metadata.get(
            "category", ""
        ),
        "url": metadata.get(
            "url", ""
        ),
        "characters": char_count,
        "words": word_count,
        "status": status,
        "issues": "; ".join(issues),
    }


def main():
    text_files = sorted(
        PROCESSED_DIR.glob("*.txt")
    )

    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Processed Source Quality Audit")
    print("=" * 60)
    print()

    print(
        f"Found {len(text_files)} "
        f"processed sources."
    )
    print()

    results = []

    for text_file in text_files:
        result = inspect_file(text_file)
        results.append(result)

        marker = (
            "[OK]"
            if result["status"] == "good"
            else "[REVIEW]"
        )

        print(
            f"{marker} "
            f"{result['source_id']} | "
            f"{result['characters']:,} chars | "
            f"{result['words']:,} words"
        )

        if result["issues"]:
            print(
                f"         Issues: "
                f"{result['issues']}"
            )

    report = pd.DataFrame(results)

    report.to_csv(
        REPORT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    good = (
        report["status"] == "good"
    ).sum()

    review = (
        report["status"] == "review"
    ).sum()

    print()
    print("=" * 60)
    print("Quality audit finished")
    print("=" * 60)
    print(f"Total processed: {len(report)}")
    print(f"Good: {good}")
    print(f"Needs review: {review}")
    print()
    print(
        f"Report saved to: "
        f"{REPORT_FILE}"
    )


if __name__ == "__main__":
    main()