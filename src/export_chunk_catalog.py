from pathlib import Path
import csv
import json


ROOT = Path(__file__).resolve().parents[1]

CHUNKS_DIR = ROOT / "data" / "chunks"
EVALUATION_DIR = ROOT / "evaluation"

OUTPUT_FILE = (
    EVALUATION_DIR
    / "chunk_catalog.csv"
)


def main():

    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Chunk Catalog Export")
    print("=" * 60)
    print()

    EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    chunk_files = sorted(
        CHUNKS_DIR.glob("*.json")
    )

    if not chunk_files:
        raise RuntimeError(
            "No chunk JSON files found."
        )

    rows = []

    for chunk_file in chunk_files:

        chunks = json.loads(
            chunk_file.read_text(
                encoding="utf-8"
            )
        )

        for chunk in chunks:

            text = str(
                chunk.get(
                    "text",
                    "",
                )
            ).strip()

            rows.append(
                {
                    "chunk_id": str(
                        chunk.get(
                            "chunk_id",
                            "",
                        )
                    ),
                    "source_id": str(
                        chunk.get(
                            "source_id",
                            "",
                        )
                    ),
                    "title": str(
                        chunk.get(
                            "title",
                            "",
                        )
                    ),
                    "provider": str(
                        chunk.get(
                            "provider",
                            "",
                        )
                    ),
                    "category": str(
                        chunk.get(
                            "category",
                            "",
                        )
                    ),
                    "url": str(
                        chunk.get(
                            "url",
                            "",
                        )
                    ),
                    "text": text,
                }
            )

    fieldnames = [
        "chunk_id",
        "source_id",
        "title",
        "provider",
        "category",
        "url",
        "text",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    print(
        f"[OK] Sources: "
        f"{len(chunk_files)}"
    )

    print(
        f"[OK] Chunks exported: "
        f"{len(rows)}"
    )

    print(
        f"[OK] Output: "
        f"{OUTPUT_FILE}"
    )

    if len(rows) != 164:
        print(
            f"[WARNING] Expected 164 chunks, "
            f"found {len(rows)}"
        )
    else:
        print(
            "[OK] Chunk count verified: 164"
        )

    print()
    print("=" * 60)
    print("Export finished")
    print("=" * 60)


if __name__ == "__main__":
    main()