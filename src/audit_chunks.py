from pathlib import Path
import json

import pandas as pd
import tiktoken


ROOT = Path(__file__).resolve().parents[1]

CHUNKS_DIR = ROOT / "data" / "chunks"
METADATA_DIR = ROOT / "data" / "metadata"

REPORT_FILE = (
    METADATA_DIR / "chunk_quality_report.csv"
)

encoding = tiktoken.get_encoding(
    "cl100k_base"
)


def main():
    chunk_files = sorted(
        CHUNKS_DIR.glob("*.json")
    )

    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Chunk Quality Audit")
    print("=" * 60)
    print()

    print(
        f"Found {len(chunk_files)} "
        f"chunk files."
    )

    print()

    results = []

    total_chunks = 0
    empty_chunks = 0
    very_short_chunks = 0
    oversized_chunks = 0

    for chunk_file in chunk_files:

        chunks = json.loads(
            chunk_file.read_text(
                encoding="utf-8"
            )
        )

        source_id = chunk_file.stem

        source_chunk_count = 0

        for chunk in chunks:

            text = (
                chunk.get("text", "")
                .strip()
            )

            token_count = len(
                encoding.encode(text)
            )

            char_count = len(text)

            status = "good"
            issues = []

            if not text:
                status = "review"
                issues.append(
                    "empty"
                )
                empty_chunks += 1

            elif token_count < 30:
                status = "review"
                issues.append(
                    "very_short"
                )
                very_short_chunks += 1

            if token_count > 650:
                status = "review"
                issues.append(
                    "oversized"
                )
                oversized_chunks += 1

            results.append(
                {
                    "source_id": (
                        chunk.get(
                            "source_id",
                            source_id,
                        )
                    ),
                    "chunk_id": (
                        chunk.get(
                            "chunk_id",
                            "",
                        )
                    ),
                    "chunk_index": (
                        chunk.get(
                            "chunk_index",
                            "",
                        )
                    ),
                    "characters": (
                        char_count
                    ),
                    "tokens": (
                        token_count
                    ),
                    "status": status,
                    "issues": (
                        "; ".join(
                            issues
                        )
                    ),
                }
            )

            total_chunks += 1
            source_chunk_count += 1

        print(
            f"[OK] {source_id} -> "
            f"{source_chunk_count} chunks"
        )

    report = pd.DataFrame(
        results
    )

    report.to_csv(
        REPORT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    review_count = (
        report["status"]
        == "review"
    ).sum()

    good_count = (
        report["status"]
        == "good"
    ).sum()

    print()
    print("=" * 60)
    print("Chunk audit finished")
    print("=" * 60)

    print(
        f"Total chunks: "
        f"{total_chunks}"
    )

    print(
        f"Good chunks: "
        f"{good_count}"
    )

    print(
        f"Needs review: "
        f"{review_count}"
    )

    print(
        f"Empty chunks: "
        f"{empty_chunks}"
    )

    print(
        f"Very short chunks: "
        f"{very_short_chunks}"
    )

    print(
        f"Oversized chunks: "
        f"{oversized_chunks}"
    )

    print()

    print(
        f"Report saved to: "
        f"{REPORT_FILE}"
    )


if __name__ == "__main__":
    main()