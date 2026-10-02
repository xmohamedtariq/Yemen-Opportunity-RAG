from pathlib import Path
import json
import logging
import os
import re

from dotenv import load_dotenv
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

from build_vector_store import (
    CohereMultilingualEmbeddings,
    EMBEDDING_MODEL,
    COLLECTION_NAME,
)


logger = logging.getLogger(
    "yemen_opportunity.retriever"
)


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = ROOT / ".env"
CHUNKS_DIR = ROOT / "data" / "chunks"
CHROMA_DIR = ROOT / "data" / "chroma"


# ---------------------------------------------------------
# Retrieval configuration
# ---------------------------------------------------------

VECTOR_K = 20
BM25_K = 20
FINAL_K = 10

RRF_CONSTANT = 60


# ---------------------------------------------------------
# Arabic + English text normalization
# ---------------------------------------------------------

def normalize_text(text):
    """
    Normalize Arabic and English text for BM25 keyword search.
    """

    text = str(text).lower()

    # Remove Arabic diacritics
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

    # Normalize common Arabic letters
    text = (
        text
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
    )

    return text


def tokenize(text):
    """
    Tokenizer suitable for basic Arabic + English BM25.
    """

    text = normalize_text(text)

    tokens = re.findall(
        r"[a-z0-9_]+|[\u0600-\u06FF]+",
        text,
    )

    return tokens


# ---------------------------------------------------------
# Load chunks
# ---------------------------------------------------------

def load_corpus():
    chunk_files = sorted(
        CHUNKS_DIR.glob("*.json")
    )

    if not chunk_files:
        raise RuntimeError(
            f"No chunks found in {CHUNKS_DIR}"
        )

    corpus = []

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
                continue

            if not chunk_id:
                continue

            corpus.append(
                {
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
                    "text": text,
                }
            )

    return corpus


# ---------------------------------------------------------
# Hybrid Retriever
# ---------------------------------------------------------

class HybridRetriever:

    def __init__(self):

        # ---------------------------------------------
        # Environment
        # ---------------------------------------------

        load_dotenv(
            ENV_FILE
        )

        api_key = os.getenv(
            "COHERE_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "COHERE_API_KEY was not found."
            )

        # ---------------------------------------------
        # Embedding model
        # ---------------------------------------------

        self.embeddings = (
            CohereMultilingualEmbeddings(
                api_key=api_key,
                model=EMBEDDING_MODEL,
            )
        )

        # ---------------------------------------------
        # Open existing Chroma database
        # ---------------------------------------------

        if not CHROMA_DIR.exists():
            raise RuntimeError(
                "Chroma database does not exist. "
                "Run build_vector_store.py first."
            )

        self.vector_store = Chroma(
            collection_name=(
                COLLECTION_NAME
            ),
            embedding_function=(
                self.embeddings
            ),
            persist_directory=str(
                CHROMA_DIR
            ),
        )

        # ---------------------------------------------
        # Load raw chunk corpus for BM25
        # ---------------------------------------------

        self.corpus = load_corpus()

        self.chunk_lookup = {
            item["chunk_id"]: item
            for item in self.corpus
        }

        tokenized_corpus = [
            tokenize(
                item["text"]
            )
            for item in self.corpus
        ]

        self.bm25 = BM25Okapi(
            tokenized_corpus
        )

        print(
            f"[OK] Loaded "
            f"{len(self.corpus)} chunks"
        )

        print(
            "[OK] Chroma vector search ready"
        )

        print(
            "[OK] BM25 keyword search ready"
        )


    # -----------------------------------------------------
    # Vector retrieval
    # -----------------------------------------------------

    def vector_search(
        self,
        query,
        k=VECTOR_K,
    ):

        documents = (
            self.vector_store
            .similarity_search(
                query,
                k=k,
            )
        )

        results = []

        for rank, document in enumerate(
            documents,
            start=1,
        ):

            metadata = document.metadata

            chunk_id = str(
                metadata.get(
                    "chunk_id",
                    "",
                )
            )

            if not chunk_id:
                continue

            results.append(
                {
                    "chunk_id": chunk_id,
                    "rank": rank,
                    "text": (
                        document.page_content
                    ),
                    "metadata": metadata,
                }
            )

        return results


    # -----------------------------------------------------
    # BM25 retrieval
    # -----------------------------------------------------

    def bm25_search(
        self,
        query,
        k=BM25_K,
    ):

        query_tokens = tokenize(
            query
        )

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )[:k]

        results = []

        for rank, index in enumerate(
            ranked_indexes,
            start=1,
        ):

            item = self.corpus[index]

            results.append(
                {
                    "chunk_id": (
                        item["chunk_id"]
                    ),
                    "rank": rank,
                    "bm25_score": float(
                        scores[index]
                    ),
                    "text": item["text"],
                    "metadata": item,
                }
            )

        return results


    # -----------------------------------------------------
    # Reciprocal Rank Fusion
    # -----------------------------------------------------

    def reciprocal_rank_fusion(
        self,
        vector_results,
        bm25_results,
        final_k=FINAL_K,
    ):

        combined = {}

        # ---------------------------------------------
        # Vector results
        # ---------------------------------------------

        for result in vector_results:

            chunk_id = result[
                "chunk_id"
            ]

            if chunk_id not in combined:

                combined[chunk_id] = {
                    "chunk_id": chunk_id,
                    "text": (
                        result["text"]
                    ),
                    "metadata": (
                        result["metadata"]
                    ),
                    "vector_rank": None,
                    "bm25_rank": None,
                    "bm25_score": None,
                    "rrf_score": 0.0,
                }

            rank = result["rank"]

            combined[
                chunk_id
            ]["vector_rank"] = rank

            combined[
                chunk_id
            ]["rrf_score"] += (
                1.0
                / (
                    RRF_CONSTANT
                    + rank
                )
            )

        # ---------------------------------------------
        # BM25 results
        # ---------------------------------------------

        for result in bm25_results:

            chunk_id = result[
                "chunk_id"
            ]

            if chunk_id not in combined:

                combined[chunk_id] = {
                    "chunk_id": chunk_id,
                    "text": (
                        result["text"]
                    ),
                    "metadata": (
                        result["metadata"]
                    ),
                    "vector_rank": None,
                    "bm25_rank": None,
                    "bm25_score": None,
                    "rrf_score": 0.0,
                }

            rank = result["rank"]

            combined[
                chunk_id
            ]["bm25_rank"] = rank

            combined[
                chunk_id
            ]["bm25_score"] = (
                result["bm25_score"]
            )

            combined[
                chunk_id
            ]["rrf_score"] += (
                1.0
                / (
                    RRF_CONSTANT
                    + rank
                )
            )

        # ---------------------------------------------
        # Sort by RRF score
        # ---------------------------------------------

        ranked = sorted(
            combined.values(),
            key=lambda item: (
                item["rrf_score"]
            ),
            reverse=True,
        )

        return ranked[:final_k]


    # -----------------------------------------------------
    # Full hybrid search
    # -----------------------------------------------------

    def search(
        self,
        query,
        vector_k=VECTOR_K,
        bm25_k=BM25_K,
        final_k=FINAL_K,
    ):

        bm25_results = (
            self.bm25_search(
                query,
                k=bm25_k,
            )
        )

        # BM25 is fully local, so keep it as a dependable fallback.
        # If query embeddings are rate-limited or the embedding API is
        # temporarily unavailable, the user should still receive useful
        # keyword-based results instead of a failed search.
        try:

            vector_results = (
                self.vector_search(
                    query,
                    k=vector_k,
                )
            )

            retrieval_mode = "hybrid"

        except Exception as error:

            logger.warning(
                "Vector search unavailable; falling back to BM25. "
                "error=%s",
                type(error).__name__,
            )

            vector_results = []
            retrieval_mode = "bm25_fallback"

        final_results = (
            self.reciprocal_rank_fusion(
                vector_results,
                bm25_results,
                final_k=final_k,
            )
        )

        for result in final_results:
            result[
                "retrieval_mode"
            ] = retrieval_mode

        return final_results


# ---------------------------------------------------------
# Display test results
# ---------------------------------------------------------

def display_results(
    query,
    results,
):

    print()
    print("=" * 70)
    print("HYBRID SEARCH TEST")
    print("=" * 70)

    print()
    print(
        f"Query: {query}"
    )

    print()

    for rank, result in enumerate(
        results,
        start=1,
    ):

        metadata = result[
            "metadata"
        ]

        preview = (
            result["text"]
            .replace(
                "\n",
                " ",
            )[:300]
        )

        print(
            f"Result {rank}"
        )

        print(
            f"Chunk ID: "
            f"{result['chunk_id']}"
        )

        print(
            f"Source ID: "
            f"{metadata.get('source_id')}"
        )

        print(
            f"Title: "
            f"{metadata.get('title')}"
        )

        print(
            f"Vector rank: "
            f"{result['vector_rank']}"
        )

        print(
            f"BM25 rank: "
            f"{result['bm25_rank']}"
        )

        print(
            f"RRF score: "
            f"{result['rrf_score']:.6f}"
        )

        print(
            f"URL: "
            f"{metadata.get('url')}"
        )

        print(
            f"Preview: "
            f"{preview}..."
        )

        print(
            "-" * 70
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print("Yemen Opportunity RAG")
    print("Hybrid Retriever")
    print("=" * 70)
    print()

    try:

        retriever = (
            HybridRetriever()
        )

    except Exception as error:

        print(
            "[ERROR] Failed to initialize "
            "retriever:"
        )

        print(
            type(error).__name__,
            str(error),
        )

        return

    # -----------------------------------------------------
    # Arabic + English test query
    # -----------------------------------------------------

    query = (
        "ما هي شروط الأهلية لبرنامج "
        "Google Summer of Code؟"
    )

    try:

        results = retriever.search(
            query=query,
            vector_k=20,
            bm25_k=20,
            final_k=10,
        )

    except Exception as error:

        print(
            "[ERROR] Hybrid search failed:"
        )

        print(
            type(error).__name__,
            str(error),
        )

        return

    display_results(
        query,
        results,
    )

    print()
    print("=" * 70)
    print("Hybrid retrieval finished")
    print("=" * 70)

    print(
        f"Vector candidates: "
        f"{VECTOR_K}"
    )

    print(
        f"BM25 candidates: "
        f"{BM25_K}"
    )

    print(
        f"Final RRF results: "
        f"{len(results)}"
    )

    print(
        f"RRF constant: "
        f"{RRF_CONSTANT}"
    )


if __name__ == "__main__":
    main()