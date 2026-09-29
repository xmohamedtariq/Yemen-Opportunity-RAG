from pathlib import Path
import json
import os
import shutil
import time

import chromadb
import cohere
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings


ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = ROOT / ".env"
CHUNKS_DIR = ROOT / "data" / "chunks"
CHROMA_DIR = ROOT / "data" / "chroma"

COLLECTION_NAME = "yemen_opportunities"
EMBEDDING_MODEL = "embed-multilingual-v3.0"

BATCH_SIZE = 40

class CohereMultilingualEmbeddings(Embeddings):
    """
    LangChain-compatible Cohere multilingual embeddings.

    Documents:
        search_document

    Queries:
        search_query
    """

    def __init__(
        self,
        api_key: str,
        model: str = "embed-multilingual-v3.0",
    ):
        self.client = cohere.ClientV2(
            api_key=api_key
        )

        self.model = model

    def embed_documents(
        self,
        texts,
    ):
        if not texts:
            return []

        response = self.client.embed(
            model=self.model,
            texts=texts,
            input_type="search_document",
            embedding_types=["float"],
        )

        return response.embeddings.float

    def embed_query(
        self,
        text,
    ):
        response = self.client.embed(
            model=self.model,
            texts=[text],
            input_type="search_query",
            embedding_types=["float"],
        )

        return response.embeddings.float[0]


def load_chunks():
    chunk_files = sorted(
        CHUNKS_DIR.glob("*.json")
    )

    if not chunk_files:
        raise RuntimeError(
            f"No chunk files found in {CHUNKS_DIR}"
        )

    ids = []
    documents = []
    metadatas = []

    for chunk_file in chunk_files:
        chunks = json.loads(
            chunk_file.read_text(
                encoding="utf-8"
            )
        )

        for chunk in chunks:
            text = str(
                chunk.get("text", "")
            ).strip()

            chunk_id = str(
                chunk.get("chunk_id", "")
            ).strip()

            if not text:
                raise ValueError(
                    f"Empty text in {chunk_file.name}"
                )

            if not chunk_id:
                raise ValueError(
                    f"Missing chunk_id in {chunk_file.name}"
                )

            metadata = {
                "chunk_id": chunk_id,
                "source_id": str(
                    chunk.get(
                        "source_id",
                        "",
                    )
                ),
                "chunk_index": int(
                    chunk.get(
                        "chunk_index",
                        0,
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
            }

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(metadata)

    if len(ids) != len(set(ids)):
        raise RuntimeError(
            "Duplicate chunk IDs detected."
        )

    return ids, documents, metadatas


def embed_documents(
    client,
    documents,
):
    all_embeddings = []

    total_batches = (
        len(documents)
        + BATCH_SIZE
        - 1
    ) // BATCH_SIZE

    for start in range(
        0,
        len(documents),
        BATCH_SIZE,
    ):
        batch = documents[
            start:start + BATCH_SIZE
        ]

        batch_number = (
            start // BATCH_SIZE
        ) + 1

        print(
            f"Embedding batch "
            f"{batch_number}/{total_batches} "
            f"({len(batch)} texts)"
        )

        response = client.embed(
            model=EMBEDDING_MODEL,
            texts=batch,
            input_type="search_document",
            embedding_types=["float"],
        )

        batch_embeddings = (
            response.embeddings.float
        )

        all_embeddings.extend(
            batch_embeddings
        )

        time.sleep(0.3)

    return all_embeddings


def main():
    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Chroma Vector Store Rebuild")
    print("=" * 60)
    print()

    load_dotenv(
        ENV_FILE
    )

    api_key = os.getenv(
        "COHERE_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "COHERE_API_KEY not found."
        )

    print(
        "[OK] COHERE_API_KEY found"
    )

    # -------------------------------------------------
    # Load chunks
    # -------------------------------------------------

    ids, documents, metadatas = (
        load_chunks()
    )

    print(
        f"[OK] Loaded {len(documents)} chunks"
    )

    if len(documents) != 164:
        print(
            f"[WARNING] Expected 164 chunks, "
            f"found {len(documents)}"
        )

    # -------------------------------------------------
    # Generate embeddings
    # -------------------------------------------------

    co = cohere.ClientV2(
        api_key=api_key
    )

    print()
    print(
        "Generating Cohere embeddings..."
    )

    embeddings = embed_documents(
        co,
        documents,
    )

    print()
    print(
        f"[OK] Generated "
        f"{len(embeddings)} embeddings"
    )

    if (
        len(embeddings)
        != len(documents)
    ):
        raise RuntimeError(
            "Embedding count does not "
            "match document count."
        )

    # -------------------------------------------------
    # Remove old broken Chroma DB
    # -------------------------------------------------

    if CHROMA_DIR.exists():
        print()
        print(
            "Removing old Chroma database..."
        )

        shutil.rmtree(
            CHROMA_DIR
        )

    CHROMA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -------------------------------------------------
    # Create persistent Chroma client
    # -------------------------------------------------

    chroma_client = (
        chromadb.PersistentClient(
            path=str(CHROMA_DIR)
        )
    )

    collection = (
        chroma_client
        .get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            },
        )
    )

    # -------------------------------------------------
    # Store in explicit batches
    # -------------------------------------------------

    print()
    print(
        "Writing vectors to Chroma..."
    )

    for start in range(
        0,
        len(documents),
        BATCH_SIZE,
    ):
        end = min(
            start + BATCH_SIZE,
            len(documents),
        )

        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )

        print(
            f"[OK] Stored "
            f"{end}/{len(documents)}"
        )

    # -------------------------------------------------
    # Critical verification
    # -------------------------------------------------

    final_count = (
        collection.count()
    )

    print()
    print("=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    print(
        f"Collection: "
        f"{COLLECTION_NAME}"
    )

    print(
        f"Stored records: "
        f"{final_count}"
    )

    if final_count != len(documents):
        raise RuntimeError(
            f"Chroma verification failed. "
            f"Expected {len(documents)}, "
            f"found {final_count}."
        )

    sample = collection.get(
        limit=1,
        include=[
            "documents",
            "metadatas",
        ],
    )

    if not sample["ids"]:
        raise RuntimeError(
            "Chroma sample check failed."
        )

    print(
        f"Sample ID: "
        f"{sample['ids'][0]}"
    )

    print(
        f"Sample title: "
        f"{sample['metadatas'][0].get('title')}"
    )

    print()
    print(
        "[SUCCESS] Chroma database "
        "contains all chunks."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()