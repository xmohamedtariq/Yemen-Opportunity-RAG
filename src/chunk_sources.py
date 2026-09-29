from pathlib import Path
import json

from langchain_text_splitters import RecursiveCharacterTextSplitter


ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"
METADATA_DIR = ROOT / "data" / "metadata"
CHUNKS_DIR = ROOT / "data" / "chunks"

CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    chunk_size=600,
    chunk_overlap=90,
    separators=[
        "\n\n",
        "\n",
        "؟ ",
        ". ",
        "؛ ",
        "، ",
        " ",
        "",
    ],
)


def chunk_source(text_file: Path) -> int:
    source_id = text_file.stem

    metadata_file = METADATA_DIR / f"{source_id}.json"

    if metadata_file.exists():
        metadata = json.loads(
            metadata_file.read_text(encoding="utf-8")
        )
    else:
        metadata = {
            "source_id": source_id
        }

    text = text_file.read_text(encoding="utf-8")

    chunks = splitter.split_text(text)

    output_data = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_id = f"{source_id}-CH-{index:03d}"

        output_data.append(
            {
                "chunk_id": chunk_id,
                "source_id": source_id,
                "chunk_index": index,
                "text": chunk,
                "title": metadata.get("title", ""),
                "provider": metadata.get("provider", ""),
                "category": metadata.get("category", ""),
                "url": metadata.get("url", ""),
            }
        )

    output_file = CHUNKS_DIR / f"{source_id}.json"

    output_file.write_text(
        json.dumps(
            output_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"[OK] {source_id} -> "
        f"{len(chunks)} chunks"
    )

    return len(chunks)


def main():
    text_files = sorted(
        PROCESSED_DIR.glob("*.txt")
    )

    print()
    print(
        f"Found {len(text_files)} "
        f"processed sources."
    )
    print()

    total_chunks = 0
    successful = 0
    failed = 0

    for text_file in text_files:
        print(f"Processing {text_file.stem}")

        try:
            count = chunk_source(text_file)
            total_chunks += count
            successful += 1

        except Exception as error:
            failed += 1
            print(
                f"[FAILED] {text_file.stem}: "
                f"{error}"
            )

        print("-" * 60)

    print()
    print("Chunking finished")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total chunks: {total_chunks}")


if __name__ == "__main__":
    main()