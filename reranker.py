from pathlib import Path
import os

import cohere
from dotenv import load_dotenv

from hybrid_retriever import HybridRetriever


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

RERANK_MODEL = "rerank-multilingual-v3.0"

HYBRID_CANDIDATES = 20
TOP_N = 5


# ---------------------------------------------------------
# Cohere Reranker
# ---------------------------------------------------------

class CohereReranker:

    def __init__(self):

        # -------------------------------------------------
        # Load environment variables
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Cohere client
        # -------------------------------------------------

        self.client = cohere.ClientV2(
            api_key=api_key
        )

        # -------------------------------------------------
        # Hybrid retriever
        # -------------------------------------------------

        self.retriever = HybridRetriever()

        print(
            "[OK] Cohere reranker ready"
        )


    # -----------------------------------------------------
    # Rerank candidate chunks
    # -----------------------------------------------------

    def rerank(
        self,
        query,
        candidates,
        top_n=TOP_N,
    ):

        if not candidates:
            return []

        # -------------------------------------------------
        # Enrich each candidate with source metadata
        #
        # This is important because a chunk from another
        # opportunity may mention the name of the opportunity
        # asked about.
        #
        # Example:
        #
        # Outreachy text may mention:
        # "Google Summer of Code"
        #
        # Adding the source title/provider/category helps the
        # reranker understand which source is actually about
        # Google Summer of Code.
        # -------------------------------------------------

        documents = []

        for candidate in candidates:

            metadata = candidate[
                "metadata"
            ]

            title = str(
                metadata.get(
                    "title",
                    "",
                )
            )

            provider = str(
                metadata.get(
                    "provider",
                    "",
                )
            )

            category = str(
                metadata.get(
                    "category",
                    "",
                )
            )

            source_id = str(
                metadata.get(
                    "source_id",
                    "",
                )
            )

            text = str(
                candidate.get(
                    "text",
                    "",
                )
            )

            enriched_document = (
                f"Source title: {title}\n"
                f"Provider: {provider}\n"
                f"Category: {category}\n"
                f"Source ID: {source_id}\n"
                f"\n"
                f"Content:\n"
                f"{text}"
            )

            documents.append(
                enriched_document
            )

        # -------------------------------------------------
        # Cohere reranking
        # -------------------------------------------------

        response = self.client.rerank(
            model=RERANK_MODEL,
            query=query,
            documents=documents,
            top_n=min(
                top_n,
                len(documents),
            ),
        )

        reranked = []

        # -------------------------------------------------
        # Map Cohere results back to original candidates
        # -------------------------------------------------

        for rerank_position, result in enumerate(
            response.results,
            start=1,
        ):

            original_index = int(
                result.index
            )

            candidate = dict(
                candidates[
                    original_index
                ]
            )

            candidate[
                "hybrid_rank"
            ] = (
                original_index + 1
            )

            candidate[
                "rerank_rank"
            ] = (
                rerank_position
            )

            candidate[
                "rerank_score"
            ] = float(
                result.relevance_score
            )

            reranked.append(
                candidate
            )

        return reranked


    # -----------------------------------------------------
    # Complete retrieval pipeline
    # -----------------------------------------------------

    def search(
        self,
        query,
        candidate_k=HYBRID_CANDIDATES,
        top_n=TOP_N,
    ):

        # -------------------------------------------------
        # Stage 1:
        # Vector Search + BM25 + RRF
        # -------------------------------------------------

        candidates = (
            self.retriever.search(
                query=query,
                vector_k=20,
                bm25_k=20,
                final_k=candidate_k,
            )
        )

        # -------------------------------------------------
        # Stage 2:
        # Cohere multilingual reranking
        # -------------------------------------------------

        reranked = self.rerank(
            query=query,
            candidates=candidates,
            top_n=top_n,
        )

        return reranked


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

def display_results(
    query,
    results,
):

    print()
    print("=" * 70)
    print("COHERE RERANKING TEST")
    print("=" * 70)

    print()
    print(
        f"Query: {query}"
    )

    print()

    if not results:

        print(
            "No results found."
        )

        return

    for result in results:

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
            f"Result "
            f"{result['rerank_rank']}"
        )

        print(
            f"Title: "
            f"{metadata.get('title')}"
        )

        print(
            f"Provider: "
            f"{metadata.get('provider')}"
        )

        print(
            f"Category: "
            f"{metadata.get('category')}"
        )

        print(
            f"Source ID: "
            f"{metadata.get('source_id')}"
        )

        print(
            f"Chunk ID: "
            f"{result['chunk_id']}"
        )

        print(
            f"Original Hybrid Rank: "
            f"{result['hybrid_rank']}"
        )

        print(
            f"Vector Rank: "
            f"{result.get('vector_rank')}"
        )

        print(
            f"BM25 Rank: "
            f"{result.get('bm25_rank')}"
        )

        print(
            f"RRF Score: "
            f"{result['rrf_score']:.6f}"
        )

        print(
            f"Rerank Score: "
            f"{result['rerank_score']:.6f}"
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
# Main test
# ---------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print("Yemen Opportunity RAG")
    print("Hybrid Retrieval + Cohere Reranking")
    print("=" * 70)
    print()

    # -----------------------------------------------------
    # Test query
    # -----------------------------------------------------

    query = (
        "ما هي شروط الأهلية لبرنامج "
        "Google Summer of Code؟"
    )

    try:

        reranker = (
            CohereReranker()
        )

        results = (
            reranker.search(
                query=query,
                candidate_k=20,
                top_n=5,
            )
        )

    except Exception as error:

        print()
        print(
            "[ERROR] Reranking failed:"
        )

        print(
            type(error).__name__,
            str(error),
        )

        return

    # -----------------------------------------------------
    # Display final results
    # -----------------------------------------------------

    display_results(
        query,
        results,
    )

    print()
    print("=" * 70)
    print("Reranking finished")
    print("=" * 70)

    print(
        f"Hybrid candidates: "
        f"{HYBRID_CANDIDATES}"
    )

    print(
        f"Final results: "
        f"{len(results)}"
    )

    print(
        f"Rerank model: "
        f"{RERANK_MODEL}"
    )


if __name__ == "__main__":
    main()