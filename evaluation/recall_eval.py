from pathlib import Path
import csv
import json
import sys
import time


# =========================================================
# UTF-8 console support for Windows
# =========================================================

try:
    sys.stdout.reconfigure(
        encoding="utf-8"
    )
except Exception:
    pass


# =========================================================
# Project paths
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = ROOT / "src"
EVALUATION_DIR = ROOT / "evaluation"

GOLDEN_FILE = (
    EVALUATION_DIR
    / "golden_questions.json"
)

RESULTS_FILE = (
    EVALUATION_DIR
    / "recall_results.csv"
)

SUMMARY_FILE = (
    EVALUATION_DIR
    / "recall_summary.md"
)


# Make src importable
sys.path.insert(
    0,
    str(SRC_DIR),
)


# =========================================================
# Project imports
# =========================================================

from reranker import CohereReranker


# =========================================================
# Evaluation configuration
# =========================================================

TOP_K = 5

VECTOR_CANDIDATES = 20
BM25_CANDIDATES = 20
HYBRID_CANDIDATES = 20

MAX_RETRIES = 5


# =========================================================
# Load golden questions
# =========================================================

def load_golden_questions():

    if not GOLDEN_FILE.exists():
        raise FileNotFoundError(
            f"Golden questions file not found: "
            f"{GOLDEN_FILE}"
        )

    with GOLDEN_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        questions = json.load(
            file
        )

    if not isinstance(
        questions,
        list,
    ):
        raise ValueError(
            "golden_questions.json must "
            "contain a JSON list."
        )

    if len(questions) != 30:
        raise ValueError(
            f"Expected 30 golden questions, "
            f"found {len(questions)}."
        )

    required_fields = {
        "id",
        "question",
        "language",
        "gold_chunk_ids",
        "gold_source_id",
        "difficulty",
    }

    seen_ids = set()

    for item in questions:

        missing = (
            required_fields
            - set(item.keys())
        )

        if missing:
            raise ValueError(
                f"{item.get('id', 'UNKNOWN')} "
                f"is missing fields: "
                f"{sorted(missing)}"
            )

        question_id = item["id"]

        if question_id in seen_ids:
            raise ValueError(
                f"Duplicate question ID: "
                f"{question_id}"
            )

        seen_ids.add(
            question_id
        )

        gold_ids = item[
            "gold_chunk_ids"
        ]

        if (
            not isinstance(
                gold_ids,
                list,
            )
            or not gold_ids
        ):
            raise ValueError(
                f"{question_id} has invalid "
                f"gold_chunk_ids."
            )

    return questions


# =========================================================
# Retry helper for API calls
# =========================================================

def retry_call(
    label,
    function,
):

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            return function()

        except Exception as error:

            last_error = error

            if attempt >= MAX_RETRIES:
                break

            wait_seconds = min(
                2 ** attempt,
                20,
            )

            print(
                f"[WARNING] {label} failed "
                f"(attempt {attempt}/"
                f"{MAX_RETRIES})."
            )

            print(
                f"          "
                f"{type(error).__name__}: "
                f"{error}"
            )

            print(
                f"          Retrying in "
                f"{wait_seconds}s..."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        f"{label} failed after "
        f"{MAX_RETRIES} attempts."
    ) from last_error


# =========================================================
# Result helpers
# =========================================================

def get_chunk_ids(
    results,
    k=TOP_K,
):

    return [
        result["chunk_id"]
        for result in results[:k]
    ]


def gold_hit(
    retrieved_ids,
    gold_ids,
):
    """
    Strict query-level Recall@5 hit.

    For normal questions there is one gold chunk.

    If a question intentionally has more than one
    required gold chunk, all listed gold chunks must
    appear in the top-k. This avoids artificially
    inflating the metric.
    """

    retrieved = set(
        retrieved_ids
    )

    gold = set(
        gold_ids
    )

    return int(
        gold.issubset(
            retrieved
        )
    )


def bool_value(
    value,
):

    return str(
        value
    ).strip().lower() in {
        "1",
        "true",
        "yes",
    }


# =========================================================
# Existing results / resume support
# =========================================================

FIELDNAMES = [
    "id",
    "language",
    "difficulty",
    "question",
    "gold_source_id",
    "gold_chunk_ids",

    "vector_top5",
    "vector_hit",

    "bm25_top5",
    "bm25_hit",

    "hybrid_top5",
    "hybrid_hit",

    "rerank_top5",
    "rerank_hit",
]


def load_existing_results():

    if not RESULTS_FILE.exists():
        return []

    with RESULTS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        return list(
            reader
        )


def save_results(
    rows,
):

    with RESULTS_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# =========================================================
# Recall calculations
# =========================================================

def calculate_recall(
    rows,
    field,
):

    if not rows:
        return 0.0

    hits = sum(
        1
        for row in rows
        if bool_value(
            row[field]
        )
    )

    return (
        hits
        / len(rows)
    )


def calculate_hits(
    rows,
    field,
):

    return sum(
        1
        for row in rows
        if bool_value(
            row[field]
        )
    )


# =========================================================
# Breakdown helper
# =========================================================

def filtered_recall(
    rows,
    field,
    key,
    value,
):

    filtered = [
        row
        for row in rows
        if row[key] == value
    ]

    if not filtered:
        return (
            0,
            0,
            0.0,
        )

    hits = calculate_hits(
        filtered,
        field,
    )

    recall = (
        hits
        / len(filtered)
    )

    return (
        hits,
        len(filtered),
        recall,
    )


# =========================================================
# Summary report
# =========================================================

def write_summary(
    rows,
):

    methods = [
        (
            "Vector Search",
            "vector_hit",
        ),
        (
            "BM25",
            "bm25_hit",
        ),
        (
            "Hybrid (Vector + BM25 + RRF)",
            "hybrid_hit",
        ),
        (
            "Hybrid + Cohere Reranker",
            "rerank_hit",
        ),
    ]

    lines = []

    lines.append(
        "# Yemen Opportunity RAG — Recall@5 Evaluation"
    )

    lines.append("")

    lines.append(
        f"Total evaluated questions: "
        f"{len(rows)}"
    )

    lines.append("")

    lines.append(
        "## Overall Results"
    )

    lines.append("")

    lines.append(
        "| Retrieval Method | Hits | Recall@5 |"
    )

    lines.append(
        "|---|---:|---:|"
    )

    for method_name, field in methods:

        hits = calculate_hits(
            rows,
            field,
        )

        recall = calculate_recall(
            rows,
            field,
        )

        lines.append(
            f"| {method_name} "
            f"| {hits}/{len(rows)} "
            f"| {recall:.2%} |"
        )

    # -----------------------------------------------------
    # Improvement calculations
    # -----------------------------------------------------

    vector_recall = calculate_recall(
        rows,
        "vector_hit",
    )

    hybrid_recall = calculate_recall(
        rows,
        "hybrid_hit",
    )

    rerank_recall = calculate_recall(
        rows,
        "rerank_hit",
    )

    lines.append("")

    lines.append(
        "## Improvements"
    )

    lines.append("")

    lines.append(
        f"- Hybrid vs Vector: "
        f"{(hybrid_recall - vector_recall) * 100:+.2f} "
        f"percentage points"
    )

    lines.append(
        f"- Reranker vs Hybrid: "
        f"{(rerank_recall - hybrid_recall) * 100:+.2f} "
        f"percentage points"
    )

    lines.append(
        f"- Final pipeline vs Vector: "
        f"{(rerank_recall - vector_recall) * 100:+.2f} "
        f"percentage points"
    )

    # -----------------------------------------------------
    # Language breakdown
    # -----------------------------------------------------

    lines.append("")

    lines.append(
        "## Final Pipeline by Language"
    )

    lines.append("")

    lines.append(
        "| Language | Hits | Recall@5 |"
    )

    lines.append(
        "|---|---:|---:|"
    )

    for language in [
        "ar",
        "en",
    ]:

        hits, total, recall = (
            filtered_recall(
                rows,
                "rerank_hit",
                "language",
                language,
            )
        )

        lines.append(
            f"| {language} "
            f"| {hits}/{total} "
            f"| {recall:.2%} |"
        )

    # -----------------------------------------------------
    # Difficulty breakdown
    # -----------------------------------------------------

    lines.append("")

    lines.append(
        "## Final Pipeline by Difficulty"
    )

    lines.append("")

    lines.append(
        "| Difficulty | Hits | Recall@5 |"
    )

    lines.append(
        "|---|---:|---:|"
    )

    for difficulty in [
        "easy",
        "medium",
        "hard",
    ]:

        hits, total, recall = (
            filtered_recall(
                rows,
                "rerank_hit",
                "difficulty",
                difficulty,
            )
        )

        lines.append(
            f"| {difficulty} "
            f"| {hits}/{total} "
            f"| {recall:.2%} |"
        )

    # -----------------------------------------------------
    # Missed questions
    # -----------------------------------------------------

    missed = [
        row
        for row in rows
        if not bool_value(
            row["rerank_hit"]
        )
    ]

    lines.append("")

    lines.append(
        "## Questions Missed by Final Pipeline"
    )

    lines.append("")

    if not missed:

        lines.append(
            "None. All gold passages were "
            "retrieved in the top 5."
        )

    else:

        for row in missed:

            lines.append(
                f"- **{row['id']}** "
                f"({row['language']}, "
                f"{row['difficulty']}): "
                f"{row['question']}"
            )

            lines.append(
                f"  - Gold: "
                f"`{row['gold_chunk_ids']}`"
            )

            lines.append(
                f"  - Retrieved: "
                f"`{row['rerank_top5']}`"
            )

    lines.append("")

    lines.append(
        "## Evaluation Definition"
    )

    lines.append("")

    lines.append(
        "Recall@5 is measured at the query level. "
        "A question counts as a hit when its required "
        "gold chunk is present among the top five "
        "retrieved chunks. For questions with multiple "
        "required gold chunks, all listed gold chunks "
        "must be present in the top five."
    )

    SUMMARY_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# =========================================================
# Main evaluation
# =========================================================

def main():

    print()
    print("=" * 72)
    print("Yemen Opportunity RAG")
    print("Day 3 - Recall@5 Evaluation")
    print("=" * 72)
    print()

    # -----------------------------------------------------
    # Load and validate golden set
    # -----------------------------------------------------

    questions = (
        load_golden_questions()
    )

    print(
        f"[OK] Golden questions loaded: "
        f"{len(questions)}"
    )

    arabic_count = sum(
        1
        for item in questions
        if item["language"] == "ar"
    )

    english_count = sum(
        1
        for item in questions
        if item["language"] == "en"
    )

    print(
        f"[OK] Arabic questions: "
        f"{arabic_count}"
    )

    print(
        f"[OK] English questions: "
        f"{english_count}"
    )

    # -----------------------------------------------------
    # Initialize retrieval system once
    # -----------------------------------------------------

    print()
    print(
        "Initializing retrieval pipeline..."
    )

    reranker = CohereReranker()

    retriever = (
        reranker.retriever
    )

    print()
    print(
        "[OK] Evaluation pipeline ready"
    )

    # -----------------------------------------------------
    # Resume support
    # -----------------------------------------------------

    rows = (
        load_existing_results()
    )

    completed_ids = {
        row["id"]
        for row in rows
    }

    if completed_ids:

        print(
            f"[INFO] Existing completed "
            f"questions: "
            f"{len(completed_ids)}"
        )

        print(
            "[INFO] They will be skipped."
        )

    # -----------------------------------------------------
    # Evaluate each question
    # -----------------------------------------------------

    for number, item in enumerate(
        questions,
        start=1,
    ):

        question_id = item["id"]

        if question_id in completed_ids:

            print()
            print(
                f"[{number:02d}/30] "
                f"{question_id} - SKIPPED"
            )

            continue

        question = item[
            "question"
        ]

        gold_ids = item[
            "gold_chunk_ids"
        ]

        print()
        print("=" * 72)

        print(
            f"[{number:02d}/30] "
            f"{question_id}"
        )

        print(
            f"Language: "
            f"{item['language']}"
        )

        print(
            f"Difficulty: "
            f"{item['difficulty']}"
        )

        print(
            f"Question: "
            f"{question}"
        )

        print(
            f"Gold: "
            f"{', '.join(gold_ids)}"
        )

        print("-" * 72)

        # -------------------------------------------------
        # 1. Vector Search
        # -------------------------------------------------

        vector_results = retry_call(
            f"{question_id} vector search",
            lambda: retriever.vector_search(
                question,
                k=VECTOR_CANDIDATES,
            ),
        )

        vector_top5 = (
            get_chunk_ids(
                vector_results,
                TOP_K,
            )
        )

        vector_hit = gold_hit(
            vector_top5,
            gold_ids,
        )

        # -------------------------------------------------
        # 2. BM25
        # -------------------------------------------------

        bm25_results = (
            retriever.bm25_search(
                question,
                k=BM25_CANDIDATES,
            )
        )

        bm25_top5 = (
            get_chunk_ids(
                bm25_results,
                TOP_K,
            )
        )

        bm25_hit = gold_hit(
            bm25_top5,
            gold_ids,
        )

        # -------------------------------------------------
        # 3. Hybrid RRF
        # -------------------------------------------------

        hybrid_results = (
            retriever
            .reciprocal_rank_fusion(
                vector_results,
                bm25_results,
                final_k=(
                    HYBRID_CANDIDATES
                ),
            )
        )

        hybrid_top5 = (
            get_chunk_ids(
                hybrid_results,
                TOP_K,
            )
        )

        hybrid_hit = gold_hit(
            hybrid_top5,
            gold_ids,
        )

        # -------------------------------------------------
        # 4. Hybrid + Reranker
        # -------------------------------------------------

        rerank_results = retry_call(
            f"{question_id} reranking",
            lambda: reranker.rerank(
                query=question,
                candidates=hybrid_results,
                top_n=TOP_K,
            ),
        )

        rerank_top5 = (
            get_chunk_ids(
                rerank_results,
                TOP_K,
            )
        )

        rerank_hit = gold_hit(
            rerank_top5,
            gold_ids,
        )

        # -------------------------------------------------
        # Display
        # -------------------------------------------------

        print(
            f"Vector @5 : "
            f"{'HIT' if vector_hit else 'MISS'}"
        )

        print(
            f"BM25 @5   : "
            f"{'HIT' if bm25_hit else 'MISS'}"
        )

        print(
            f"Hybrid @5 : "
            f"{'HIT' if hybrid_hit else 'MISS'}"
        )

        print(
            f"Rerank @5 : "
            f"{'HIT' if rerank_hit else 'MISS'}"
        )

        # -------------------------------------------------
        # Save result
        # -------------------------------------------------

        row = {
            "id": question_id,
            "language": (
                item["language"]
            ),
            "difficulty": (
                item["difficulty"]
            ),
            "question": question,
            "gold_source_id": (
                item["gold_source_id"]
            ),
            "gold_chunk_ids": "|".join(
                gold_ids
            ),

            "vector_top5": "|".join(
                vector_top5
            ),
            "vector_hit": vector_hit,

            "bm25_top5": "|".join(
                bm25_top5
            ),
            "bm25_hit": bm25_hit,

            "hybrid_top5": "|".join(
                hybrid_top5
            ),
            "hybrid_hit": hybrid_hit,

            "rerank_top5": "|".join(
                rerank_top5
            ),
            "rerank_hit": rerank_hit,
        }

        rows.append(
            row
        )

        completed_ids.add(
            question_id
        )

        # Save after EVERY question
        # so progress is not lost.
        save_results(
            rows
        )

        # Be gentle with API limits.
        time.sleep(
            0.5
        )

    # =====================================================
    # Final validation
    # =====================================================

    rows = sorted(
        rows,
        key=lambda row: row["id"],
    )

    save_results(
        rows
    )

    print()
    print("=" * 72)
    print("FINAL RECALL@5 RESULTS")
    print("=" * 72)
    print()

    if len(rows) != 30:

        print(
            f"[WARNING] Only "
            f"{len(rows)}/30 questions "
            f"were evaluated."
        )

    methods = [
        (
            "Vector Search",
            "vector_hit",
        ),
        (
            "BM25",
            "bm25_hit",
        ),
        (
            "Hybrid",
            "hybrid_hit",
        ),
        (
            "Hybrid + Reranker",
            "rerank_hit",
        ),
    ]

    for name, field in methods:

        hits = calculate_hits(
            rows,
            field,
        )

        recall = calculate_recall(
            rows,
            field,
        )

        print(
            f"{name:<22} "
            f"{hits:>2}/{len(rows)} "
            f"= {recall:.2%}"
        )

    # -----------------------------------------------------
    # Report
    # -----------------------------------------------------

    write_summary(
        rows
    )

    print()
    print(
        f"[OK] Detailed results:"
    )

    print(
        RESULTS_FILE
    )

    print()
    print(
        f"[OK] Summary report:"
    )

    print(
        SUMMARY_FILE
    )

    print()
    print("=" * 72)
    print("Recall@5 evaluation finished")
    print("=" * 72)


if __name__ == "__main__":
    main()