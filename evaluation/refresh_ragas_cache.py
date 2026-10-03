import json
import os
import sys
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
EVALUATION_DIR = ROOT_DIR / "evaluation"

CACHE_PATH = (
    EVALUATION_DIR
    / "ragas_dataset_cache.json"
)


# ============================================================
# IMPORT PROJECT CODE
# ============================================================

sys.path.insert(
    0,
    str(SRC_DIR),
)

sys.path.insert(
    0,
    str(EVALUATION_DIR),
)


# The cached RAGAS dataset was built from the evaluated two-pass
# generation path. Preserve that default for reproducible refreshes.
os.environ.setdefault(
    "RAG_ENABLE_ANSWER_REVIEW",
    "1",
)


from rag_pipeline import YemenOpportunityRAG
from ragas_eval import extract_used_contexts


# ============================================================
# LOAD CACHE
# ============================================================

def load_cache():

    if not CACHE_PATH.exists():

        raise FileNotFoundError(
            f"Cache not found: {CACHE_PATH}"
        )

    with open(
        CACHE_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        rows = json.load(
            file
        )

    if not isinstance(
        rows,
        list,
    ):

        raise ValueError(
            "RAGAS cache must contain a JSON list."
        )

    return rows


# ============================================================
# SAVE CACHE
# ============================================================

def save_cache(
    rows,
):

    with open(
        CACHE_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            rows,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print("Yemen Opportunity RAG")
    print("Refresh Production Answers Only")
    print("=" * 72)
    print()

    rows = load_cache()

    print(
        f"[OK] Cached samples loaded: "
        f"{len(rows)}"
    )

    print(
        "[INFO] Existing reference answers "
        "will NOT be changed."
    )

    print(
        "[INFO] Only production answers, "
        "retrieved contexts, and latency "
        "will be refreshed."
    )

    print()

    rag = YemenOpportunityRAG()

    print()

    for index, row in enumerate(
        rows,
        start=1,
    ):

        question_id = (
            row.get(
                "id",
                f"Q{index:02d}",
            )
        )

        question = (
            row.get(
                "user_input",
                "",
            )
        ).strip()

        if not question:

            raise RuntimeError(
                f"Missing user_input for "
                f"{question_id}"
            )

        # Preserve existing reference exactly.
        old_reference = (
            row.get(
                "reference"
            )
        )

        old_gold_contexts = (
            row.get(
                "gold_contexts"
            )
        )

        old_gold_chunk_ids = (
            row.get(
                "gold_chunk_ids"
            )
        )

        print(
            f"[{index:02d}/{len(rows):02d}] "
            f"{question_id}"
        )

        print(
            "   -> Running updated "
            "evaluated RAG benchmark path..."
        )

        result = (
            rag.ask(
                question
            )
        )

        answer = str(
            result.get(
                "answer",
                "",
            )
        ).strip()

        if not answer:

            raise RuntimeError(
                f"Empty answer for "
                f"{question_id}"
            )

        contexts = (
            extract_used_contexts(
                rag,
                result,
            )
        )

        if not contexts:

            raise RuntimeError(
                f"No contexts returned for "
                f"{question_id}"
            )

        # Update ONLY production-side fields.
        row[
            "response"
        ] = answer

        row[
            "retrieved_contexts"
        ] = contexts

        row[
            "latency_seconds"
        ] = result.get(
            "latency_seconds"
        )

        # Explicitly preserve evaluation ground truth.
        row[
            "reference"
        ] = old_reference

        row[
            "gold_contexts"
        ] = old_gold_contexts

        row[
            "gold_chunk_ids"
        ] = old_gold_chunk_ids

        # Save after every question.
        save_cache(
            rows
        )

        print(
            f"   [OK] Contexts: "
            f"{len(contexts)}"
        )

        print(
            f"   [OK] Latency: "
            f"{result.get('latency_seconds')}s"
        )

        print(
            "   [OK] Reference preserved"
        )

        print()

    print("=" * 72)
    print(
        "All 20 production answers refreshed."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()