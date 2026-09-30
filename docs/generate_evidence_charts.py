from __future__ import annotations

from pathlib import Path
import math
import re

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

EVALUATION_DIR = ROOT / "evaluation"
DOCS_DIR = ROOT / "docs"
CHARTS_DIR = DOCS_DIR / "charts"

RECALL_SUMMARY = EVALUATION_DIR / "recall_summary.md"
RAGAS_SUMMARY = EVALUATION_DIR / "ragas_summary.md"
COST_SUMMARY = EVALUATION_DIR / "investor_cost_summary.md"


# ============================================================
# HELPERS
# ============================================================

def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


def markdown_row(
    text: str,
    first_column: str,
) -> list[str]:
    """
    Return the first Markdown table row whose first column
    exactly matches first_column.
    """

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line.startswith("|"):
            continue

        columns = [
            column.strip()
            for column in line.strip("|").split("|")
        ]

        if (
            columns
            and columns[0] == first_column
        ):
            return columns

    raise ValueError(
        f"Could not find Markdown row: "
        f"{first_column!r}"
    )


def percent_value(value: str) -> float:
    return float(
        value.replace("%", "").strip()
    )


def money_value(value: str) -> float:
    return float(
        value.replace("$", "")
        .replace(",", "")
        .strip()
    )


def number_value(value: str) -> float:
    cleaned = re.sub(
        r"[^0-9.\-]",
        "",
        value,
    )

    return float(cleaned)


def finish_figure(
    fig,
    output_path: Path,
):
    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        f"[OK] {output_path.relative_to(ROOT)}"
    )


def add_horizontal_labels(
    ax,
    bars,
    formatter,
):
    for bar in bars:

        value = bar.get_width()

        ax.text(
            value,
            bar.get_y()
            + bar.get_height() / 2,
            f"  {formatter(value)}",
            va="center",
            fontsize=10,
        )


# ============================================================
# 1. RECALL@5
# ============================================================

def generate_recall_chart(
    recall_text: str,
):
    source_labels = [
        "Vector Search",
        "BM25",
        "Hybrid (Vector + BM25 + RRF)",
        "Hybrid + Cohere Reranker",
    ]

    display_labels = [
        "Vector Search",
        "BM25",
        "Hybrid + RRF",
        "Hybrid + Reranker",
    ]

    values = []

    for label in source_labels:

        row = markdown_row(
            recall_text,
            label,
        )

        values.append(
            percent_value(
                row[-1]
            )
        )

    fig, ax = plt.subplots(
        figsize=(10, 5.8)
    )

    bars = ax.barh(
        display_labels,
        values,
    )

    ax.set_title(
        "Retrieval Quality — Recall@5",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Recall@5 (%)"
    )

    ax.set_xlim(
        0,
        110,
    )

    ax.grid(
        axis="x",
        alpha=0.25,
    )

    add_horizontal_labels(
        ax,
        bars,
        lambda value: f"{value:.2f}%",
    )

    ax.text(
        0.01,
        -0.18,
        (
            "Final pipeline retrieved every required "
            "gold passage in the top five: 30/30 questions."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "recall_at_5.png",
    )


# ============================================================
# 2. RAGAS
# ============================================================

def generate_ragas_chart(
    ragas_text: str,
):
    source_labels = [
        "Faithfulness",
        "Answer Relevancy",
        "Llm Context Precision With Reference",
        "Context Recall",
    ]

    display_labels = [
        "Faithfulness",
        "Answer Relevancy",
        "Context Precision",
        "Context Recall",
    ]

    values = []

    for label in source_labels:

        row = markdown_row(
            ragas_text,
            label,
        )

        values.append(
            float(row[-1])
        )

    fig, ax = plt.subplots(
        figsize=(10, 5.8)
    )

    bars = ax.barh(
        display_labels,
        values,
    )

    ax.set_title(
        "RAGAS Quality Metrics",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Score (0–1)"
    )

    ax.set_xlim(
        0,
        1.10,
    )

    ax.grid(
        axis="x",
        alpha=0.25,
    )

    add_horizontal_labels(
        ax,
        bars,
        lambda value: f"{value:.4f}",
    )

    overall_row = markdown_row(
        ragas_text,
        "**Overall mean (project summary)**",
    )

    overall = float(
        overall_row[-1]
        .replace("**", "")
        .strip()
    )

    ax.axvline(
        overall,
        linestyle="--",
        linewidth=1.5,
        label=f"Project mean = {overall:.4f}",
    )

    ax.legend(
        loc="lower right"
    )

    ax.text(
        0.01,
        -0.18,
        (
            "Context Precision and Context Recall reached 1.0. "
            "Answer Relevancy is the principal remaining weakness."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "ragas_metrics.png",
    )


# ============================================================
# 3. COST SCALING
# ============================================================

def generate_cost_scaling_chart(
    cost_text: str,
):
    mean_cost = money_value(
        markdown_row(
            cost_text,
            "Mean",
        )[-1]
    )

    p95_cost = money_value(
        markdown_row(
            cost_text,
            "P95",
        )[-1]
    )

    max_cost = money_value(
        markdown_row(
            cost_text,
            "Maximum observed",
        )[-1]
    )

    volumes = [
        1_000,
        10_000,
        100_000,
        1_000_000,
    ]

    mean_values = [
        mean_cost * volume
        for volume in volumes
    ]

    p95_values = [
        p95_cost * volume
        for volume in volumes
    ]

    max_values = [
        max_cost * volume
        for volume in volumes
    ]

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.plot(
        volumes,
        mean_values,
        marker="o",
        linewidth=2,
        label="Mean",
    )

    ax.plot(
        volumes,
        p95_values,
        marker="o",
        linewidth=2,
        label="P95",
    )

    ax.plot(
        volumes,
        max_values,
        marker="o",
        linewidth=2,
        label="Maximum observed",
    )

    ax.set_xscale(
        "log"
    )

    ax.set_yscale(
        "log"
    )

    ax.set_title(
        "Command A Generation Cost vs Query Volume",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Queries per month — logarithmic scale"
    )

    ax.set_ylabel(
        "Monthly generation cost (USD) — logarithmic scale"
    )

    ax.set_xticks(
        volumes
    )

    ax.set_xticklabels(
        [
            "1K",
            "10K",
            "100K",
            "1M",
        ]
    )

    ax.yaxis.set_major_formatter(
        mticker.StrMethodFormatter(
            "${x:,.0f}"
        )
    )

    ax.grid(
        alpha=0.25,
        which="both",
    )

    ax.legend()

    ax.text(
        0.01,
        -0.19,
        (
            "Generation-only projection. Embed, Rerank, "
            "hosting and database costs are accounted for separately."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "cost_scaling.png",
    )


# ============================================================
# 4. LATENCY PROFILE
# ============================================================

def generate_latency_chart(
    cost_text: str,
):
    row = markdown_row(
        cost_text,
        "Latency (seconds)",
    )

    labels = [
        "Mean",
        "P50",
        "P95",
        "Maximum",
    ]

    values = [
        number_value(row[1]),
        number_value(row[2]),
        number_value(row[3]),
        number_value(row[4]),
    ]

    fig, ax = plt.subplots(
        figsize=(10, 5.8)
    )

    bars = ax.barh(
        labels,
        values,
    )

    ax.set_title(
        "End-to-End RAG Latency Profile",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Seconds"
    )

    ax.grid(
        axis="x",
        alpha=0.25,
    )

    ax.set_xlim(
        0,
        max(values) * 1.18,
    )

    add_horizontal_labels(
        ax,
        bars,
        lambda value: f"{value:.3f}s",
    )

    ax.text(
        0.01,
        -0.18,
        (
            "Maximum latency includes observed network/retry effects "
            "and is not equivalent to steady-state model latency."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "latency_profile.png",
    )


# ============================================================
# LANGUAGE TABLE PARSER
# ============================================================

def get_language_rows(
    cost_text: str,
):
    arabic = markdown_row(
        cost_text,
        "ar",
    )

    english = markdown_row(
        cost_text,
        "en",
    )

    return (
        arabic,
        english,
    )


# ============================================================
# 5. LANGUAGE COST
# ============================================================

def generate_language_cost_chart(
    cost_text: str,
):
    arabic, english = (
        get_language_rows(
            cost_text
        )
    )

    labels = [
        "Arabic",
        "English",
    ]

    values = [
        money_value(
            arabic[2]
        ),
        money_value(
            english[2]
        ),
    ]

    fig, ax = plt.subplots(
        figsize=(8.5, 5.5)
    )

    bars = ax.bar(
        labels,
        values,
    )

    ax.set_title(
        "Mean Generation Cost by Query Language",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_ylabel(
        "USD per query"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    ax.set_ylim(
        0,
        max(values) * 1.25,
    )

    for bar, value in zip(
        bars,
        values,
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height(),
            f"${value:.8f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    difference_percent = (
        (
            values[0]
            / values[1]
        )
        - 1
    ) * 100

    ax.text(
        0.01,
        -0.16,
        (
            f"Observed sample: Arabic mean generation cost was "
            f"{difference_percent:.2f}% higher than English. "
            "This is a benchmark observation, not a universal rule."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "language_cost.png",
    )


# ============================================================
# 6. LANGUAGE LATENCY
# ============================================================

def generate_language_latency_chart(
    cost_text: str,
):
    arabic, english = (
        get_language_rows(
            cost_text
        )
    )

    labels = [
        "Arabic",
        "English",
    ]

    values = [
        number_value(
            arabic[4]
        ),
        number_value(
            english[4]
        ),
    ]

    fig, ax = plt.subplots(
        figsize=(8.5, 5.5)
    )

    bars = ax.bar(
        labels,
        values,
    )

    ax.set_title(
        "Mean End-to-End Latency by Query Language",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_ylabel(
        "Seconds"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    ax.set_ylim(
        0,
        max(values) * 1.25,
    )

    for bar, value in zip(
        bars,
        values,
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.3f}s",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    difference_percent = (
        (
            values[0]
            / values[1]
        )
        - 1
    ) * 100

    ax.text(
        0.01,
        -0.16,
        (
            f"Observed sample: Arabic mean end-to-end latency was "
            f"{difference_percent:.2f}% higher than English."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "language_latency.png",
    )


# ============================================================
# 7. QUALITY SUMMARY
# ============================================================

def generate_quality_summary_chart(
    recall_text: str,
    ragas_text: str,
):
    final_recall = percent_value(
        markdown_row(
            recall_text,
            "Hybrid + Cohere Reranker",
        )[-1]
    ) / 100.0

    faithfulness = float(
        markdown_row(
            ragas_text,
            "Faithfulness",
        )[-1]
    )

    relevancy = float(
        markdown_row(
            ragas_text,
            "Answer Relevancy",
        )[-1]
    )

    precision = float(
        markdown_row(
            ragas_text,
            "Llm Context Precision With Reference",
        )[-1]
    )

    context_recall = float(
        markdown_row(
            ragas_text,
            "Context Recall",
        )[-1]
    )

    labels = [
        "Recall@5",
        "Faithfulness",
        "Answer Relevancy",
        "Context Precision",
        "Context Recall",
    ]

    values = [
        final_recall,
        faithfulness,
        relevancy,
        precision,
        context_recall,
    ]

    fig, ax = plt.subplots(
        figsize=(10.5, 6)
    )

    bars = ax.barh(
        labels,
        values,
    )

    ax.set_title(
        "Yemen Opportunity Navigator — Quality Evidence",
        fontsize=16,
        pad=16,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Score (0–1)"
    )

    ax.set_xlim(
        0,
        1.10,
    )

    ax.grid(
        axis="x",
        alpha=0.25,
    )

    add_horizontal_labels(
        ax,
        bars,
        lambda value: f"{value:.4f}",
    )

    ax.text(
        0.01,
        -0.18,
        (
            "Recall@5 is based on 30 golden questions. "
            "RAGAS metrics are based on 20 questions."
        ),
        transform=ax.transAxes,
        fontsize=9,
    )

    finish_figure(
        fig,
        CHARTS_DIR / "quality_summary.png",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    CHARTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 72)
    print("Yemen Opportunity Navigator")
    print("Evidence Chart Generator")
    print("=" * 72)
    print()

    recall_text = read_text(
        RECALL_SUMMARY
    )

    ragas_text = read_text(
        RAGAS_SUMMARY
    )

    cost_text = read_text(
        COST_SUMMARY
    )

    generate_recall_chart(
        recall_text
    )

    generate_ragas_chart(
        ragas_text
    )

    generate_cost_scaling_chart(
        cost_text
    )

    generate_latency_chart(
        cost_text
    )

    generate_language_cost_chart(
        cost_text
    )

    generate_language_latency_chart(
        cost_text
    )

    generate_quality_summary_chart(
        recall_text,
        ragas_text,
    )

    print()
    print("=" * 72)
    print("COMPLETE")
    print("=" * 72)
    print()

    print(
        f"Charts directory: {CHARTS_DIR}"
    )

    print()
    print(
        "Generated charts:"
    )

    for path in sorted(
        CHARTS_DIR.glob("*.png")
    ):

        print(
            f" - {path.name}"
        )


if __name__ == "__main__":
    main()