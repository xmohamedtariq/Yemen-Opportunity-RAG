from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import math
import os
import statistics
import sys
import time

import cohere


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVALUATION_DIR = ROOT / "evaluation"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

from rag_pipeline import YemenOpportunityRAG  # noqa: E402


# ============================================================
# FILES
# ============================================================

GOLDEN_FILE = EVALUATION_DIR / "golden_questions.json"
OUTPUT_CSV = EVALUATION_DIR / "investor_cost_profile.csv"
OUTPUT_SUMMARY = EVALUATION_DIR / "investor_cost_summary.md"


# ============================================================
# VERIFIED COMMAND A PRICING SNAPSHOT
# 2026-09-30
# ============================================================

DEFAULT_COMMAND_INPUT_PRICE_PER_M = 2.50
DEFAULT_COMMAND_OUTPUT_PRICE_PER_M = 10.00


# ============================================================
# HELPERS
# ============================================================

def env_float(name: str):
    value = os.getenv(name, "").strip()
    return float(value) if value else None


def get_attr(obj, name, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def extract_billed_units(response):
    """
    Extract billed usage from Cohere Chat, Embed, or Rerank responses.

    Supported layouts:
      response.usage.billed_units
      response.meta.billed_units
    """

    usage = get_attr(response, "usage")
    meta = get_attr(response, "meta")

    billed = get_attr(usage, "billed_units")

    if billed is None:
        billed = get_attr(meta, "billed_units")

    if billed is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "search_units": 0,
        }

    return {
        "input_tokens": int(
            get_attr(billed, "input_tokens", 0) or 0
        ),
        "output_tokens": int(
            get_attr(billed, "output_tokens", 0) or 0
        ),
        "search_units": int(
            get_attr(billed, "search_units", 0) or 0
        ),
    }


def nearest_rank_percentile(values, percentile):
    if not values:
        return 0.0

    ordered = sorted(values)

    rank = math.ceil(
        percentile * len(ordered)
    )

    rank = max(
        1,
        min(rank, len(ordered)),
    )

    return ordered[rank - 1]


def safe_float(value):
    try:
        if value in ("", None):
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def format_money(value, decimals=8):
    if value is None:
        return "N/A"

    return f"${value:.{decimals}f}"


def is_retryable_error(exc: Exception) -> bool:
    """
    The production RAG already retries internally.

    This second layer retries the whole golden question when
    a transient network/API problem still escapes the internal
    retry layer.
    """

    message = (
        f"{type(exc).__name__}: {exc}"
    ).lower()

    retry_markers = [
        "getaddrinfo failed",
        "connection",
        "connecterror",
        "server disconnected",
        "remoteprotocolerror",
        "network",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "bad gateway",
        "service unavailable",
        "gateway timeout",
        "rate limit",
        "too many requests",
        "no valid response generated",
        "retrieval and reranking failed",
        "answer generation failed",
        "answer refinement failed",
        "failed after 4 attempts",
        "429",
        "502",
        "503",
        "504",
    ]

    return any(
        marker in message
        for marker in retry_markers
    )


# ============================================================
# CSV STORAGE
# ============================================================

CSV_FIELDS = [
    "id",
    "language",
    "difficulty",
    "status",

    "chat_calls",
    "chat_input_tokens",
    "chat_output_tokens",

    "embed_calls",
    "embed_input_tokens",

    "rerank_calls",
    "rerank_search_units",

    "generation_cost_usd",
    "embedding_cost_usd",
    "rerank_cost_usd",
    "total_variable_cost_usd",

    "latency_seconds",

    "answer_chars",
    "source_count",
    "retrieved_chunk_count",

    "error",
]


def load_existing_rows():
    if not OUTPUT_CSV.exists():
        return []

    with OUTPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def load_successful_rows_only():
    """
    Resume behavior:

    - keep every successful question;
    - discard old ERROR rows;
    - therefore only missing/failed questions run again.
    """

    successful_by_id = {}

    for row in load_existing_rows():

        if row.get("status") != "OK":
            continue

        question_id = str(
            row.get("id", "")
        ).strip()

        if question_id:
            successful_by_id[
                question_id
            ] = row

    return list(
        successful_by_id.values()
    )


def replace_row(rows, new_row):
    """
    Ensure only one row exists for each golden-question ID.
    """

    question_id = new_row.get("id")

    rows = [
        row
        for row in rows
        if row.get("id") != question_id
    ]

    rows.append(new_row)

    return rows


def write_rows(rows):
    rows = sorted(
        rows,
        key=lambda row: row.get(
            "id",
            "",
        ),
    )

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# STATISTICS
# ============================================================

def numeric_values(rows, key):
    values = []

    for row in rows:

        value = safe_float(
            row.get(key)
        )

        if value is not None:
            values.append(value)

    return values


def metric_stats(rows, key):
    values = numeric_values(
        rows,
        key,
    )

    if not values:
        return None

    return {
        "mean": statistics.mean(values),

        "p50": statistics.median(values),

        "p95": nearest_rank_percentile(
            values,
            0.95,
        ),

        "max": max(values),

        "min": min(values),
    }


def group_rows(rows, key):
    groups = {}

    for row in rows:

        name = (
            row.get(
                key,
                "unknown",
            )
            or "unknown"
        )

        groups.setdefault(
            name,
            [],
        ).append(row)

    return groups


# ============================================================
# MARKDOWN SUMMARY
# ============================================================

def write_summary(rows, args):

    successful = [
        row
        for row in rows
        if row.get("status") == "OK"
    ]

    failed = [
        row
        for row in rows
        if row.get("status") != "OK"
    ]

    generation_stats = metric_stats(
        successful,
        "generation_cost_usd",
    )

    total_stats = metric_stats(
        successful,
        "total_variable_cost_usd",
    )

    input_stats = metric_stats(
        successful,
        "chat_input_tokens",
    )

    output_stats = metric_stats(
        successful,
        "chat_output_tokens",
    )

    embed_stats = metric_stats(
        successful,
        "embed_input_tokens",
    )

    rerank_stats = metric_stats(
        successful,
        "rerank_search_units",
    )

    latency_stats = metric_stats(
        successful,
        "latency_seconds",
    )

    chat_call_stats = metric_stats(
        successful,
        "chat_calls",
    )

    embed_call_stats = metric_stats(
        successful,
        "embed_calls",
    )

    rerank_call_stats = metric_stats(
        successful,
        "rerank_calls",
    )

    lines = [
        "# Yemen Opportunity Navigator — Investor Cost Profile",
        "",
        "**Pricing snapshot: 2026-09-30**",
        "",
        (
            "This report measures actual API usage from the "
            "production RAG pipeline across the project's "
            "30-question golden set."
        ),
        "",
        "## 1. Measurement Status",
        "",
        f"- Golden questions recorded: {len(rows)}",
        f"- Successful measurements: {len(successful)}",
        f"- Failed measurements: {len(failed)}",
        "",
        "## 2. Pricing Inputs",
        "",
        "| Component | Rate used | Status |",
        "|---|---:|---|",
        (
            f"| Command A input | "
            f"${args.command_input_price:.4f} / 1M tokens | "
            f"Verified pricing input |"
        ),
        (
            f"| Command A output | "
            f"${args.command_output_price:.4f} / 1M tokens | "
            f"Verified pricing input |"
        ),
    ]

    # --------------------------------------------------------
    # EMBEDDING PRICE
    # --------------------------------------------------------

    if (
        args.embed_price_per_million
        is None
    ):

        lines.append(
            "| Embed Multilingual v3.0 | "
            "Not supplied | "
            "Measured usage only |"
        )

    else:

        lines.append(
            f"| Embed Multilingual v3.0 | "
            f"${args.embed_price_per_million:.6f} / 1M tokens | "
            f"Pricing supplied at runtime |"
        )

    # --------------------------------------------------------
    # RERANK PRICE
    # --------------------------------------------------------

    if (
        args.rerank_price_per_1000
        is None
    ):

        lines.append(
            "| Rerank Multilingual v3.0 | "
            "Not supplied | "
            "Measured search units only |"
        )

    else:

        lines.append(
            f"| Rerank Multilingual v3.0 | "
            f"${args.rerank_price_per_1000:.6f} "
            f"/ 1,000 searches | "
            f"Pricing supplied at runtime |"
        )

    lines.extend(
        [
            "",
            (
                "No unverified Embed or Rerank price is "
                "silently inserted into this report."
            ),
            "",
            "## 3. Measured API Usage Distribution",
            "",
            "| Metric | Mean | P50 | P95 | Maximum |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    # --------------------------------------------------------
    # DISTRIBUTION TABLE
    # --------------------------------------------------------

    metric_rows = [
        (
            "Command A input tokens",
            input_stats,
            2,
        ),
        (
            "Command A output tokens",
            output_stats,
            2,
        ),
        (
            "Embedding input tokens",
            embed_stats,
            2,
        ),
        (
            "Rerank search units",
            rerank_stats,
            2,
        ),
        (
            "Chat calls/query",
            chat_call_stats,
            2,
        ),
        (
            "Embed calls/query",
            embed_call_stats,
            2,
        ),
        (
            "Rerank calls/query",
            rerank_call_stats,
            2,
        ),
        (
            "Latency (seconds)",
            latency_stats,
            3,
        ),
    ]

    for (
        label,
        stats,
        decimals,
    ) in metric_rows:

        if stats is None:
            continue

        lines.append(
            f"| {label} | "
            f"{stats['mean']:.{decimals}f} | "
            f"{stats['p50']:.{decimals}f} | "
            f"{stats['p95']:.{decimals}f} | "
            f"{stats['max']:.{decimals}f} |"
        )

    lines.extend(
        [
            "",
            (
                "P95 uses the conservative "
                "nearest-rank method."
            ),
            "",
            "## 4. Generation Cost Distribution",
            "",
        ]
    )

    # --------------------------------------------------------
    # GENERATION COST
    # --------------------------------------------------------

    if generation_stats is not None:

        lines.extend(
            [
                "| Metric | USD/query |",
                "|---|---:|",

                (
                    f"| Mean | "
                    f"{format_money(generation_stats['mean'])} |"
                ),

                (
                    f"| P50 | "
                    f"{format_money(generation_stats['p50'])} |"
                ),

                (
                    f"| P95 | "
                    f"{format_money(generation_stats['p95'])} |"
                ),

                (
                    f"| Maximum observed | "
                    f"{format_money(generation_stats['max'])} |"
                ),

                "",
            ]
        )

    # --------------------------------------------------------
    # FULL VARIABLE COST
    # --------------------------------------------------------

    if total_stats is not None:

        lines.extend(
            [
                "## 5. Full Variable API Cost Distribution",
                "",

                "| Metric | USD/query |",
                "|---|---:|",

                (
                    f"| Mean | "
                    f"{format_money(total_stats['mean'])} |"
                ),

                (
                    f"| P50 | "
                    f"{format_money(total_stats['p50'])} |"
                ),

                (
                    f"| P95 | "
                    f"{format_money(total_stats['p95'])} |"
                ),

                (
                    f"| Maximum observed | "
                    f"{format_money(total_stats['max'])} |"
                ),

                "",
            ]
        )

    else:

        lines.extend(
            [
                "## 5. Full Variable API Cost",
                "",
                (
                    "A full API cost is intentionally not "
                    "calculated because verified Embed and/or "
                    "Rerank rates were not supplied."
                ),
                "",
                (
                    "Raw measured token and search-unit usage "
                    "is preserved so the report can be "
                    "recalculated immediately when those rates "
                    "are verified."
                ),
                "",
            ]
        )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    lines.extend(
        [
            "## 6. Cost by Language",
            "",

            (
                "| Language | N | Mean generation cost | "
                "P95 generation cost | Mean latency |"
            ),

            "|---|---:|---:|---:|---:|",
        ]
    )

    for (
        name,
        group,
    ) in sorted(
        group_rows(
            successful,
            "language",
        ).items()
    ):

        cost = metric_stats(
            group,
            "generation_cost_usd",
        )

        latency = metric_stats(
            group,
            "latency_seconds",
        )

        if (
            cost is None
            or latency is None
        ):
            continue

        lines.append(
            f"| {name} | "
            f"{len(group)} | "
            f"{format_money(cost['mean'])} | "
            f"{format_money(cost['p95'])} | "
            f"{latency['mean']:.3f}s |"
        )

    # --------------------------------------------------------
    # DIFFICULTY
    # --------------------------------------------------------

    lines.extend(
        [
            "",
            "## 7. Cost by Difficulty",
            "",

            (
                "| Difficulty | N | Mean generation cost | "
                "P95 generation cost | Mean latency |"
            ),

            "|---|---:|---:|---:|---:|",
        ]
    )

    for (
        name,
        group,
    ) in sorted(
        group_rows(
            successful,
            "difficulty",
        ).items()
    ):

        cost = metric_stats(
            group,
            "generation_cost_usd",
        )

        latency = metric_stats(
            group,
            "latency_seconds",
        )

        if (
            cost is None
            or latency is None
        ):
            continue

        lines.append(
            f"| {name} | "
            f"{len(group)} | "
            f"{format_money(cost['mean'])} | "
            f"{format_money(cost['p95'])} | "
            f"{latency['mean']:.3f}s |"
        )

    # --------------------------------------------------------
    # MONTHLY VOLUME
    # --------------------------------------------------------

    lines.extend(
        [
            "",
            "## 8. Monthly Volume Projections",
            "",
        ]
    )

    volumes = [
        1_000,
        10_000,
        100_000,
        1_000_000,
    ]

    if total_stats is not None:

        projection_stats = (
            total_stats
        )

        projection_name = (
            "Full variable API cost"
        )

    else:

        projection_stats = (
            generation_stats
        )

        projection_name = (
            "Generation-only cost"
        )

    if projection_stats is not None:

        lines.extend(
            [
                (
                    f"Projection basis: "
                    f"**{projection_name}**."
                ),

                "",

                (
                    "| Queries/month | Expected (Mean) | "
                    "Conservative (P95) | "
                    "Stress (Max observed) |"
                ),

                "|---:|---:|---:|---:|",
            ]
        )

        for volume in volumes:

            expected = (
                projection_stats["mean"]
                * volume
            )

            conservative = (
                projection_stats["p95"]
                * volume
            )

            stress = (
                projection_stats["max"]
                * volume
            )

            lines.append(
                f"| {volume:,} | "
                f"${expected:,.2f} | "
                f"${conservative:,.2f} | "
                f"${stress:,.2f} |"
            )

        lines.append("")

    # --------------------------------------------------------
    # BENCHMARK TOTAL
    # --------------------------------------------------------

    generation_total = sum(
        numeric_values(
            successful,
            "generation_cost_usd",
        )
    )

    lines.extend(
        [
            "## 9. Benchmark Run Cost",
            "",

            (
                "Measured Command A generation cost "
                "for all successful benchmark queries: "
                f"**${generation_total:.6f}**."
            ),

            "",
        ]
    )

    full_cost_values = numeric_values(
        successful,
        "total_variable_cost_usd",
    )

    if full_cost_values:

        lines.extend(
            [
                (
                    "Measured full variable API cost "
                    "for all successful benchmark queries: "
                    f"**${sum(full_cost_values):.6f}**."
                ),

                "",
            ]
        )

    # --------------------------------------------------------
    # FAILURES
    # --------------------------------------------------------

    if failed:

        lines.extend(
            [
                "## 10. Failed Measurements",
                "",
            ]
        )

        for row in failed:

            lines.append(
                f"- {row.get('id')}: "
                f"{row.get('error', 'Unknown error')}"
            )

        lines.append("")

    # --------------------------------------------------------
    # METHODOLOGY
    # --------------------------------------------------------

    lines.extend(
        [
            "## 11. Methodology Notes",
            "",

            (
                "- Every question is sent through the real "
                "production `YemenOpportunityRAG.ask()` path."
            ),

            (
                "- Chat, Embed, and Rerank billed units are "
                "read from Cohere API responses."
            ),

            (
                "- Successful measurements are cached in the "
                "CSV and are not rerun during resume."
            ),

            (
                "- Failed measurements are discarded on "
                "resume and automatically attempted again."
            ),

            (
                "- The script includes question-level retries "
                "in addition to retries already implemented "
                "inside the production RAG pipeline."
            ),

            (
                "- Latency is measured around the complete "
                "production RAG request."
            ),

            (
                "- Mean represents expected average cost."
            ),

            (
                "- P95 represents a conservative planning case."
            ),

            (
                "- Maximum observed cost represents the "
                "measured stress case."
            ),

            (
                "- Hosting, database, support, domain, taxes, "
                "monitoring, and other fixed costs are "
                "intentionally modeled separately from "
                "per-query AI API COGS."
            ),

            (
                "- Offline RAGAS evaluation cost is not "
                "treated as recurring production query cost."
            ),

            "",
        ]
    )

    OUTPUT_SUMMARY.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Measure investor-grade production RAG "
            "API usage across the golden set."
        )
    )

    parser.add_argument(
        "--fresh",
        action="store_true",
        help=(
            "Delete previous profiling results "
            "and run all questions again."
        ),
    )

    parser.add_argument(
        "--command-input-price",
        type=float,
        default=(
            DEFAULT_COMMAND_INPUT_PRICE_PER_M
        ),
        help=(
            "Command A input price per 1M tokens."
        ),
    )

    parser.add_argument(
        "--command-output-price",
        type=float,
        default=(
            DEFAULT_COMMAND_OUTPUT_PRICE_PER_M
        ),
        help=(
            "Command A output price per 1M tokens."
        ),
    )

    parser.add_argument(
        "--embed-price-per-million",
        type=float,
        default=env_float(
            "COHERE_EMBED_PRICE_PER_MILLION"
        ),
        help=(
            "Verified embedding price per 1M tokens. "
            "Leave unset until independently verified."
        ),
    )

    parser.add_argument(
        "--rerank-price-per-1000",
        type=float,
        default=env_float(
            "COHERE_RERANK_PRICE_PER_1000"
        ),
        help=(
            "Verified rerank price per 1,000 searches. "
            "Leave unset until independently verified."
        ),
    )

    parser.add_argument(
        "--min-query-seconds",
        type=float,
        default=6.5,
        help=(
            "Minimum spacing between uncached "
            "golden questions."
        ),
    )

    parser.add_argument(
        "--question-attempts",
        type=int,
        default=3,
        help=(
            "Maximum script-level attempts "
            "for one failed question."
        ),
    )

    parser.add_argument(
        "--question-retry-delay",
        type=float,
        default=15.0,
        help=(
            "Base delay in seconds between "
            "question-level retries."
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # WINDOWS UTF-8
    # --------------------------------------------------------

    try:

        sys.stdout.reconfigure(
            encoding="utf-8"
        )

    except Exception:
        pass

    # --------------------------------------------------------
    # VALIDATE GOLDEN SET
    # --------------------------------------------------------

    if not GOLDEN_FILE.exists():

        raise FileNotFoundError(
            f"Golden set not found: "
            f"{GOLDEN_FILE}"
        )

    questions = json.loads(
        GOLDEN_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        questions,
        list,
    ):

        raise ValueError(
            "golden_questions.json "
            "must contain a list."
        )

    if len(questions) != 30:

        print(
            "[WARNING] Expected 30 golden questions, "
            f"found {len(questions)}."
        )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    print("=" * 78)

    print(
        "Yemen Opportunity Navigator"
    )

    print(
        "Investor-Grade Cost Profiling"
    )

    print("=" * 78)

    print()

    print(
        f"[INFO] Golden questions: "
        f"{len(questions)}"
    )

    print(
        "[INFO] Command A input price: "
        f"${args.command_input_price}/1M"
    )

    print(
        "[INFO] Command A output price: "
        f"${args.command_output_price}/1M"
    )

    if (
        args.embed_price_per_million
        is None
    ):

        print(
            "[INFO] Embed price: "
            "NOT SUPPLIED "
            "(usage will still be measured)"
        )

    else:

        print(
            "[INFO] Embed price: "
            f"${args.embed_price_per_million}/1M"
        )

    if (
        args.rerank_price_per_1000
        is None
    ):

        print(
            "[INFO] Rerank price: "
            "NOT SUPPLIED "
            "(search units will still be measured)"
        )

    else:

        print(
            "[INFO] Rerank price: "
            f"${args.rerank_price_per_1000}"
            "/1K searches"
        )

    print()

    # ========================================================
    # LOAD / RESUME
    # ========================================================

    if args.fresh:

        if OUTPUT_CSV.exists():
            OUTPUT_CSV.unlink()

        if OUTPUT_SUMMARY.exists():
            OUTPUT_SUMMARY.unlink()

        rows = []

        print(
            "[INFO] Fresh mode: "
            "previous profiling results removed."
        )

    else:

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Keep only successful rows.
        #
        # If Q01 and Q02 failed previously while Q03-Q30
        # succeeded, Q03-Q30 stay cached and ONLY Q01/Q02
        # run again.
        # ----------------------------------------------------

        rows = (
            load_successful_rows_only()
        )

        # Remove stale ERROR rows from the CSV immediately.
        write_rows(rows)

        print(
            "[INFO] Resume mode: "
            f"{len(rows)} successful "
            "questions already cached."
        )

    completed_ids = {
        row["id"]
        for row in rows
        if row.get("status") == "OK"
    }

    # ========================================================
    # GLOBAL API USAGE TRACKER
    # ========================================================

    tracker = {
        "chat": [],
        "embed": [],
        "rerank": [],
    }

    # ========================================================
    # PATCH COHERE EMBEDDING
    # ========================================================

    original_embed = (
        cohere.ClientV2.embed
    )

    def tracked_embed(
        self,
        *call_args,
        **call_kwargs,
    ):

        response = original_embed(
            self,
            *call_args,
            **call_kwargs,
        )

        tracker[
            "embed"
        ].append(
            extract_billed_units(
                response
            )
        )

        return response

    cohere.ClientV2.embed = (
        tracked_embed
    )

    # ========================================================
    # PATCH COHERE RERANK
    # ========================================================

    original_rerank = (
        cohere.ClientV2.rerank
    )

    def tracked_rerank(
        self,
        *call_args,
        **call_kwargs,
    ):

        response = original_rerank(
            self,
            *call_args,
            **call_kwargs,
        )

        tracker[
            "rerank"
        ].append(
            extract_billed_units(
                response
            )
        )

        return response

    cohere.ClientV2.rerank = (
        tracked_rerank
    )

    # ========================================================
    # INITIALIZE REAL PRODUCTION RAG
    # ========================================================

    print(
        "[INFO] Initializing production RAG..."
    )

    rag = YemenOpportunityRAG()

    print(
        "[OK] Production RAG ready."
    )

    print()

    # ========================================================
    # PATCH PRODUCTION CHAT CLIENT
    # ========================================================

    original_chat = (
        rag.client.chat
    )

    def tracked_chat(
        *call_args,
        **call_kwargs,
    ):

        response = original_chat(
            *call_args,
            **call_kwargs,
        )

        tracker[
            "chat"
        ].append(
            extract_billed_units(
                response
            )
        )

        return response

    rag.client.chat = tracked_chat

    # ========================================================
    # RUN GOLDEN SET
    # ========================================================

    total_questions = len(
        questions
    )

    for (
        index,
        item,
    ) in enumerate(
        questions,
        start=1,
    ):

        question_id = str(
            item.get(
                "id",
                f"Q{index:02d}",
            )
        )

        # ----------------------------------------------------
        # ALREADY SUCCESSFUL
        # ----------------------------------------------------

        if question_id in completed_ids:

            print(
                f"[{index:02d}/"
                f"{total_questions:02d}] "
                f"{question_id} - CACHED"
            )

            continue

        question = str(
            item.get(
                "question",
                "",
            )
        ).strip()

        language = str(
            item.get(
                "language",
                "unknown",
            )
        )

        difficulty = str(
            item.get(
                "difficulty",
                "unknown",
            )
        )

        print(
            f"[{index:02d}/"
            f"{total_questions:02d}] "
            f"{question_id} | "
            f"{language} | "
            f"{difficulty}"
        )

        success_row = None
        final_exception = None
        final_latency = 0.0

        max_attempts = max(
            1,
            args.question_attempts,
        )

        # ====================================================
        # WHOLE-QUESTION RETRIES
        # ====================================================

        for outer_attempt in range(
            1,
            max_attempts + 1,
        ):

            tracker[
                "chat"
            ].clear()

            tracker[
                "embed"
            ].clear()

            tracker[
                "rerank"
            ].clear()

            request_started = (
                time.perf_counter()
            )

            try:

                result = rag.ask(
                    question
                )

                latency = (
                    time.perf_counter()
                    - request_started
                )

                final_latency = latency

                # --------------------------------------------
                # CHAT TOKENS
                # --------------------------------------------

                chat_input_tokens = sum(
                    call[
                        "input_tokens"
                    ]
                    for call
                    in tracker["chat"]
                )

                chat_output_tokens = sum(
                    call[
                        "output_tokens"
                    ]
                    for call
                    in tracker["chat"]
                )

                # --------------------------------------------
                # EMBEDDING TOKENS
                # --------------------------------------------

                embed_input_tokens = sum(
                    call[
                        "input_tokens"
                    ]
                    for call
                    in tracker["embed"]
                )

                # --------------------------------------------
                # RERANK SEARCH UNITS
                # --------------------------------------------

                rerank_search_units = sum(
                    call[
                        "search_units"
                    ]
                    for call
                    in tracker["rerank"]
                )

                # --------------------------------------------
                # COMMAND A COST
                # --------------------------------------------

                generation_cost = (
                    (
                        chat_input_tokens
                        / 1_000_000
                    )
                    * args.command_input_price
                    +
                    (
                        chat_output_tokens
                        / 1_000_000
                    )
                    * args.command_output_price
                )

                # --------------------------------------------
                # EMBEDDING COST
                # --------------------------------------------

                embedding_cost = None

                if (
                    args.embed_price_per_million
                    is not None
                ):

                    embedding_cost = (
                        embed_input_tokens
                        / 1_000_000
                        * args.embed_price_per_million
                    )

                # --------------------------------------------
                # RERANK COST
                # --------------------------------------------

                rerank_cost = None

                if (
                    args.rerank_price_per_1000
                    is not None
                ):

                    rerank_cost = (
                        rerank_search_units
                        / 1_000
                        * args.rerank_price_per_1000
                    )

                # --------------------------------------------
                # TOTAL VARIABLE API COST
                # --------------------------------------------

                total_variable_cost = None

                if (
                    embedding_cost is not None
                    and rerank_cost is not None
                ):

                    total_variable_cost = (
                        generation_cost
                        + embedding_cost
                        + rerank_cost
                    )

                # --------------------------------------------
                # OUTPUT METADATA
                # --------------------------------------------

                answer = str(
                    result.get(
                        "answer",
                        "",
                    )
                )

                sources = (
                    result.get(
                        "sources"
                    )
                    or []
                )

                retrieved_chunks = (
                    result.get(
                        "retrieved_chunks"
                    )
                    or []
                )

                # --------------------------------------------
                # SUCCESS ROW
                # --------------------------------------------

                success_row = {
                    "id": question_id,

                    "language": language,

                    "difficulty": difficulty,

                    "status": "OK",

                    "chat_calls": str(
                        len(
                            tracker[
                                "chat"
                            ]
                        )
                    ),

                    "chat_input_tokens": str(
                        chat_input_tokens
                    ),

                    "chat_output_tokens": str(
                        chat_output_tokens
                    ),

                    "embed_calls": str(
                        len(
                            tracker[
                                "embed"
                            ]
                        )
                    ),

                    "embed_input_tokens": str(
                        embed_input_tokens
                    ),

                    "rerank_calls": str(
                        len(
                            tracker[
                                "rerank"
                            ]
                        )
                    ),

                    "rerank_search_units": str(
                        rerank_search_units
                    ),

                    "generation_cost_usd": (
                        f"{generation_cost:.10f}"
                    ),

                    "embedding_cost_usd": (
                        ""
                        if embedding_cost is None
                        else (
                            f"{embedding_cost:.10f}"
                        )
                    ),

                    "rerank_cost_usd": (
                        ""
                        if rerank_cost is None
                        else (
                            f"{rerank_cost:.10f}"
                        )
                    ),

                    "total_variable_cost_usd": (
                        ""
                        if total_variable_cost is None
                        else (
                            f"{total_variable_cost:.10f}"
                        )
                    ),

                    "latency_seconds": (
                        f"{latency:.6f}"
                    ),

                    "answer_chars": str(
                        len(answer)
                    ),

                    "source_count": str(
                        len(sources)
                    ),

                    "retrieved_chunk_count": str(
                        len(
                            retrieved_chunks
                        )
                    ),

                    "error": "",
                }

                # --------------------------------------------
                # SAVE SUCCESS IMMEDIATELY
                # --------------------------------------------

                rows = replace_row(
                    rows,
                    success_row,
                )

                write_rows(
                    rows
                )

                completed_ids.add(
                    question_id
                )

                print(
                    "    [OK] "
                    f"chat="
                    f"{len(tracker['chat'])} | "
                    f"input="
                    f"{chat_input_tokens} | "
                    f"output="
                    f"{chat_output_tokens} | "
                    f"embed="
                    f"{embed_input_tokens} | "
                    f"rerank="
                    f"{rerank_search_units} | "
                    f"gen_cost="
                    f"${generation_cost:.6f} | "
                    f"latency="
                    f"{latency:.2f}s"
                )

                # Successful question:
                # leave outer retry loop.
                break

            except Exception as exc:

                final_exception = exc

                final_latency = (
                    time.perf_counter()
                    - request_started
                )

                print(
                    "    [QUESTION ATTEMPT "
                    f"{outer_attempt}/"
                    f"{max_attempts} FAILED] "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                retryable = (
                    is_retryable_error(
                        exc
                    )
                )

                # --------------------------------------------
                # QUESTION-LEVEL RETRY
                # --------------------------------------------

                if (
                    outer_attempt
                    < max_attempts
                    and retryable
                ):

                    wait_seconds = (
                        args.question_retry_delay
                        * outer_attempt
                    )

                    print(
                        "    [RETRY] Waiting "
                        f"{wait_seconds:.0f}s "
                        "before retrying this question..."
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                break

        # ====================================================
        # FINAL FAILURE
        # ====================================================

        if success_row is None:

            error_text = (
                (
                    f"{type(final_exception).__name__}: "
                    f"{final_exception}"
                )
                if final_exception
                is not None
                else "Unknown error"
            )

            error_row = {
                "id": question_id,

                "language": language,

                "difficulty": difficulty,

                "status": "ERROR",

                "chat_calls": str(
                    len(
                        tracker[
                            "chat"
                        ]
                    )
                ),

                "chat_input_tokens": "",

                "chat_output_tokens": "",

                "embed_calls": str(
                    len(
                        tracker[
                            "embed"
                        ]
                    )
                ),

                "embed_input_tokens": "",

                "rerank_calls": str(
                    len(
                        tracker[
                            "rerank"
                        ]
                    )
                ),

                "rerank_search_units": "",

                "generation_cost_usd": "",

                "embedding_cost_usd": "",

                "rerank_cost_usd": "",

                "total_variable_cost_usd": "",

                "latency_seconds": (
                    f"{final_latency:.6f}"
                ),

                "answer_chars": "",

                "source_count": "",

                "retrieved_chunk_count": "",

                "error": error_text,
            }

            rows = replace_row(
                rows,
                error_row,
            )

            write_rows(
                rows
            )

            print(
                "    [FINAL ERROR] "
                f"{error_text}"
            )

        # ====================================================
        # RATE-LIMIT FRIENDLY SPACING
        # ====================================================

        if (
            final_latency
            < args.min_query_seconds
        ):

            time.sleep(
                args.min_query_seconds
                - final_latency
            )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    write_summary(
        rows,
        args,
    )

    successful = [
        row
        for row in rows
        if row.get("status") == "OK"
    ]

    failed = [
        row
        for row in rows
        if row.get("status") != "OK"
    ]

    generation_costs = numeric_values(
        successful,
        "generation_cost_usd",
    )

    print()

    print("=" * 78)

    print(
        "INVESTOR COST PROFILE COMPLETE"
    )

    print("=" * 78)

    print(
        f"Successful queries: "
        f"{len(successful)}/"
        f"{len(questions)}"
    )

    print(
        f"Failed queries:     "
        f"{len(failed)}"
    )

    if generation_costs:

        mean_generation_cost = (
            statistics.mean(
                generation_costs
            )
        )

        p50_generation_cost = (
            statistics.median(
                generation_costs
            )
        )

        p95_generation_cost = (
            nearest_rank_percentile(
                generation_costs,
                0.95,
            )
        )

        max_generation_cost = (
            max(
                generation_costs
            )
        )

        print(
            "Mean generation cost/query: "
            f"${mean_generation_cost:.8f}"
        )

        print(
            "P50 generation cost/query:  "
            f"${p50_generation_cost:.8f}"
        )

        print(
            "P95 generation cost/query:  "
            f"${p95_generation_cost:.8f}"
        )

        print(
            "Max generation cost/query:  "
            f"${max_generation_cost:.8f}"
        )

    print()

    print(
        "CSV:"
    )

    print(
        OUTPUT_CSV
    )

    print()

    print(
        "Summary:"
    )

    print(
        OUTPUT_SUMMARY
    )

    if failed:

        print()

        print(
            "[INFO] Some questions are still missing."
        )

        print(
            "[INFO] Run this same command again "
            "WITHOUT --fresh."
        )

        print(
            "[INFO] Successful questions remain cached; "
            "only failed questions will run again."
        )


if __name__ == "__main__":
    main()