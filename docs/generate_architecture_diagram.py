from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

CHARTS_DIR = ROOT / "docs" / "charts"

PNG_OUTPUT = (
    CHARTS_DIR
    / "architecture_diagram.png"
)

SVG_OUTPUT = (
    CHARTS_DIR
    / "architecture_diagram.svg"
)


# ============================================================
# VISUAL CONSTANTS
# ============================================================

LINE_COLOR = "#303030"
TEXT_COLOR = "#202020"


# ============================================================
# DRAWING HELPERS
# ============================================================

def component_box(
    ax,
    x,
    y,
    width,
    height,
    title,
    subtitle="",
    title_size=10,
    subtitle_size=7.5,
):
    """
    Draw one rounded architecture component.
    """

    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=(
            "round,pad=0.35,"
            "rounding_size=1.1"
        ),
        linewidth=1.4,
        edgecolor=LINE_COLOR,
        facecolor="white",
    )

    ax.add_patch(
        patch
    )

    ax.text(
        x + width / 2,
        y + height * 0.62,
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        fontweight="bold",
        color=TEXT_COLOR,
    )

    if subtitle:

        ax.text(
            x + width / 2,
            y + height * 0.30,
            subtitle,
            ha="center",
            va="center",
            fontsize=subtitle_size,
            color=TEXT_COLOR,
        )

    return {
        "x": x,
        "y": y,
        "w": width,
        "h": height,
    }


def left(component):
    return (
        component["x"],
        component["y"]
        + component["h"] / 2,
    )


def right(component):
    return (
        component["x"]
        + component["w"],
        component["y"]
        + component["h"] / 2,
    )


def top(component):
    return (
        component["x"]
        + component["w"] / 2,
        component["y"]
        + component["h"],
    )


def bottom(component):
    return (
        component["x"]
        + component["w"] / 2,
        component["y"],
    )


def direct_arrow(
    ax,
    start,
    end,
):
    """
    Draw a simple straight arrow.
    """

    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "->",
            "linewidth": 1.25,
            "color": LINE_COLOR,
        },
    )


def routed_arrow(
    ax,
    points,
    label=None,
    label_position=None,
):
    """
    Draw a routed multi-segment connection.

    points example:
        [
            (x1, y1),
            (x2, y2),
            (x3, y3),
        ]

    The final segment receives the arrow head.
    """

    if len(points) < 2:
        return

    xs = [
        point[0]
        for point in points
    ]

    ys = [
        point[1]
        for point in points
    ]

    if len(points) > 2:

        ax.plot(
            xs[:-1],
            ys[:-1],
            linewidth=1.15,
            color=LINE_COLOR,
        )

    ax.annotate(
        "",
        xy=points[-1],
        xytext=points[-2],
        arrowprops={
            "arrowstyle": "->",
            "linewidth": 1.25,
            "color": LINE_COLOR,
        },
    )

    if (
        label
        and label_position
    ):

        ax.text(
            label_position[0],
            label_position[1],
            label,
            fontsize=7,
            ha="center",
            va="center",
            color=TEXT_COLOR,
        )


def section_title(
    ax,
    x,
    y,
    title,
):
    """
    Draw section heading.
    """

    ax.text(
        x,
        y,
        title,
        fontsize=12.5,
        fontweight="bold",
        ha="left",
        va="center",
        color=TEXT_COLOR,
    )


def evidence_box(
    ax,
    x,
    title,
    value,
    note,
):
    """
    Draw one measured-evidence card.
    """

    width = 17
    y = 2
    height = 6.5

    patch = component_box(
        ax,
        x,
        y,
        width,
        height,
        title,
        value,
        title_size=8.8,
        subtitle_size=8,
    )

    ax.text(
        x + width / 2,
        y + 0.35,
        note,
        fontsize=6.2,
        ha="center",
        va="bottom",
        color=TEXT_COLOR,
    )

    return patch


# ============================================================
# ARCHITECTURE DIAGRAM
# ============================================================

def generate_architecture_diagram():

    CHARTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(20, 12)
    )

    ax.set_xlim(
        0,
        120,
    )

    ax.set_ylim(
        0,
        100,
    )

    ax.axis(
        "off"
    )

    # ========================================================
    # TITLE
    # ========================================================

    ax.text(
        60,
        97,
        "Yemen Opportunity Navigator",
        fontsize=22,
        fontweight="bold",
        ha="center",
        va="center",
        color=TEXT_COLOR,
    )

    ax.text(
        60,
        94,
        (
            "Evidence-Based Retrieval-Augmented "
            "Generation Architecture"
        ),
        fontsize=12,
        ha="center",
        va="center",
        color=TEXT_COLOR,
    )

    # ========================================================
    # A. KNOWLEDGE BASE / OFFLINE INGESTION
    # ========================================================

    section_title(
        ax,
        2,
        90,
        "A. Knowledge Base / Offline Ingestion",
    )

    # --------------------------------------------------------
    # Official sources
    # --------------------------------------------------------

    sources = component_box(
        ax,
        2,
        79,
        12,
        8,
        "Official Sources",
        "49 processed source records",
    )

    # --------------------------------------------------------
    # Fetch and parse
    # --------------------------------------------------------

    fetch_parse = component_box(
        ax,
        18,
        79,
        12,
        8,
        "Fetch + Parse",
        "Official source content",
    )

    # --------------------------------------------------------
    # Clean and chunk
    # --------------------------------------------------------

    clean_chunk = component_box(
        ax,
        34,
        79,
        12,
        8,
        "Clean + Chunk",
        "Normalized text + metadata",
    )

    # --------------------------------------------------------
    # Chunk corpus
    # --------------------------------------------------------

    chunks = component_box(
        ax,
        50,
        79,
        12,
        8,
        "Chunk Corpus",
        "164 searchable chunks",
    )

    # --------------------------------------------------------
    # Document embeddings
    # --------------------------------------------------------

    embeddings = component_box(
        ax,
        66,
        79,
        13,
        8,
        "Embeddings",
        "embed-multilingual-v3.0",
    )

    # --------------------------------------------------------
    # Chroma
    # --------------------------------------------------------

    chroma = component_box(
        ax,
        83,
        79,
        13,
        8,
        "Chroma",
        "Persistent vector store",
    )

    # --------------------------------------------------------
    # Main ingestion flow
    # --------------------------------------------------------

    direct_arrow(
        ax,
        right(sources),
        left(fetch_parse),
    )

    direct_arrow(
        ax,
        right(fetch_parse),
        left(clean_chunk),
    )

    direct_arrow(
        ax,
        right(clean_chunk),
        left(chunks),
    )

    direct_arrow(
        ax,
        right(chunks),
        left(embeddings),
    )

    direct_arrow(
        ax,
        right(embeddings),
        left(chroma),
    )

    # ========================================================
    # OFFLINE BM25 INDEX
    # ========================================================

    bm25_index = component_box(
        ax,
        50,
        68,
        14,
        7,
        "BM25 Index",
        "Arabic + English lexical index",
    )

    direct_arrow(
        ax,
        bottom(chunks),
        top(bm25_index),
    )

    ax.text(
        57,
        76.4,
        "same chunk corpus",
        fontsize=6.8,
        ha="center",
        color=TEXT_COLOR,
    )

    # ========================================================
    # B. ONLINE QUERY PIPELINE
    # ========================================================

    section_title(
        ax,
        2,
        64,
        "B. Online Query Pipeline",
    )

    # --------------------------------------------------------
    # User
    # --------------------------------------------------------

    user = component_box(
        ax,
        2,
        53,
        11,
        8,
        "User",
        "Arabic / English query",
    )

    # --------------------------------------------------------
    # Streamlit
    # --------------------------------------------------------

    streamlit = component_box(
        ax,
        16,
        53,
        13,
        8,
        "Streamlit UI",
        "Query + answer interface",
    )

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    auth = component_box(
        ax,
        16,
        42,
        13,
        7,
        "Supabase Auth",
        "Sign up / login / session",
    )

    # --------------------------------------------------------
    # Query object
    # --------------------------------------------------------

    query = component_box(
        ax,
        32,
        53,
        11,
        8,
        "Query",
        "Language detected",
    )

    # --------------------------------------------------------
    # User -> Streamlit -> Query
    # --------------------------------------------------------

    direct_arrow(
        ax,
        right(user),
        left(streamlit),
    )

    direct_arrow(
        ax,
        right(streamlit),
        left(query),
    )

    # --------------------------------------------------------
    # Streamlit -> Supabase authentication
    # --------------------------------------------------------

    direct_arrow(
        ax,
        bottom(streamlit),
        top(auth),
    )

    ax.text(
        22.5,
        50.3,
        "authentication",
        fontsize=6.7,
        ha="center",
        color=TEXT_COLOR,
    )

    # ========================================================
    # RETRIEVAL BRANCH 1 — VECTOR SEARCH
    # ========================================================

    query_embedding = component_box(
        ax,
        47,
        53,
        14,
        8,
        "Query Embedding",
        "input_type = search_query",
    )

    vector_search = component_box(
        ax,
        66,
        53,
        13,
        8,
        "Vector Search",
        "Chroma similarity search",
    )

    direct_arrow(
        ax,
        right(query),
        left(query_embedding),
    )

    direct_arrow(
        ax,
        right(query_embedding),
        left(vector_search),
    )

    # ========================================================
    # RETRIEVAL BRANCH 2 — BM25
    # ========================================================

    bm25_search = component_box(
        ax,
        47,
        42,
        14,
        8,
        "BM25 Search",
        "Lexical keyword retrieval",
    )

    # --------------------------------------------------------
    # Raw query text goes directly to BM25.
    # It DOES NOT pass through the embedding model.
    # --------------------------------------------------------

    routed_arrow(
        ax,
        [
            bottom(query),

            (
                bottom(query)[0],
                46,
            ),

            left(bm25_search),
        ],

        label="raw query text",

        label_position=(
            39,
            46.8,
        ),
    )

    # ========================================================
    # CHROMA STORE -> VECTOR SEARCH
    # ========================================================

    routed_arrow(
        ax,
        [
            bottom(chroma),

            (
                bottom(chroma)[0],
                65,
            ),

            (
                top(vector_search)[0],
                65,
            ),

            top(vector_search),
        ],

        label="persistent vectors",

        label_position=(
            83,
            66,
        ),
    )

    # ========================================================
    # BM25 INDEX -> BM25 SEARCH
    # ========================================================

    # This route intentionally travels around the
    # Query Embedding component so the diagram does
    # not imply any dependency between BM25 and embeddings.

    routed_arrow(
        ax,
        [
            bottom(bm25_index),

            (
                63.5,
                bottom(bm25_index)[1],
            ),

            (
                63.5,
                51.5,
            ),

            (
                top(bm25_search)[0],
                51.5,
            ),

            top(bm25_search),
        ],

        label="lexical index",

        label_position=(
            64.5,
            59,
        ),
    )

    # ========================================================
    # HYBRID + RRF
    # ========================================================

    hybrid = component_box(
        ax,
        66,
        42,
        13,
        8,
        "Hybrid + RRF",
        "Merge ranked candidates",
    )

    # Vector search -> Hybrid
    direct_arrow(
        ax,
        bottom(vector_search),
        top(hybrid),
    )

    # BM25 search -> Hybrid
    direct_arrow(
        ax,
        right(bm25_search),
        left(hybrid),
    )

    # ========================================================
    # TOP-20 HYBRID CANDIDATES
    # ========================================================

    candidates = component_box(
        ax,
        83,
        42,
        12,
        8,
        "Candidates",
        "Top 20 hybrid chunks",
    )

    direct_arrow(
        ax,
        right(hybrid),
        left(candidates),
    )

    # ========================================================
    # COHERE RERANKER
    # ========================================================

    reranker = component_box(
        ax,
        99,
        42,
        14,
        8,
        "Cohere Reranker",
        "rerank-multilingual-v3.0",
    )

    direct_arrow(
        ax,
        right(candidates),
        left(reranker),
    )

    # ========================================================
    # TOP-5 EVIDENCE
    # ========================================================

    top5 = component_box(
        ax,
        101,
        31,
        10,
        7,
        "Top 5",
        "Evidence chunks",
    )

    direct_arrow(
        ax,
        bottom(reranker),
        top(top5),
    )

    # ========================================================
    # GENERATION PIPELINE
    # ========================================================

    # --------------------------------------------------------
    # Context Builder
    # --------------------------------------------------------

    context = component_box(
        ax,
        54,
        23,
        13,
        8,
        "Context Builder",
        "Chunk text + metadata",
    )

    # --------------------------------------------------------
    # First Command A pass
    # --------------------------------------------------------

    draft = component_box(
        ax,
        70,
        23,
        13,
        8,
        "Command A",
        "Pass 1: grounded draft",
    )

    # --------------------------------------------------------
    # Second Command A pass
    # --------------------------------------------------------

    review = component_box(
        ax,
        86,
        23,
        13,
        8,
        "Command A",
        "Pass 2: draft + context review",
    )

    # ========================================================
    # SOURCE BUILDER
    # ========================================================

    source_builder = component_box(
        ax,
        102,
        21,
        14,
        7,
        "Source Builder",
        "Source attribution metadata",
    )

    # ========================================================
    # ANSWER CLEANUP
    # ========================================================

    cleanup = component_box(
        ax,
        86,
        12,
        13,
        8,
        "Answer Cleanup",
        "Public-safe formatting",
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    final_output = component_box(
        ax,
        102,
        12,
        14,
        8,
        "Final Output",
        "Answer + sources in UI",
    )

    # ========================================================
    # TOP-5 -> CONTEXT BUILDER
    # ========================================================

    routed_arrow(
        ax,
        [
            left(top5),

            (
                98.5,
                left(top5)[1],
            ),

            (
                98.5,
                34.5,
            ),

            (
                right(context)[0] + 1.5,
                34.5,
            ),

            (
                right(context)[0] + 1.5,
                right(context)[1],
            ),

            right(context),
        ],

        label="Top-5 retrieved evidence",

        label_position=(
            80,
            35.3,
        ),
    )

    # ========================================================
    # TOP-5 -> SOURCE BUILDER
    # ========================================================

    direct_arrow(
        ax,
        bottom(top5),
        top(source_builder),
    )

    # ========================================================
    # CONTEXT -> DRAFT -> REVIEW
    # ========================================================

    direct_arrow(
        ax,
        right(context),
        left(draft),
    )

    direct_arrow(
        ax,
        right(draft),
        left(review),
    )

    # ========================================================
    # REVIEW -> ANSWER CLEANUP
    # ========================================================

    direct_arrow(
        ax,
        bottom(review),
        top(cleanup),
    )

    # ========================================================
    # ANSWER CLEANUP -> FINAL OUTPUT
    # ========================================================

    direct_arrow(
        ax,
        right(cleanup),
        left(final_output),
    )

    # ========================================================
    # SOURCE BUILDER -> FINAL OUTPUT
    # ========================================================

    direct_arrow(
        ax,
        bottom(source_builder),
        top(final_output),
    )

    # ========================================================
    # C. MEASURED EVIDENCE
    # ========================================================

    section_title(
        ax,
        2,
        10,
        "C. Measured Evidence",
    )

    # --------------------------------------------------------
    # Recall@5
    # --------------------------------------------------------

    evidence_box(
        ax,
        2,
        "Recall@5",
        "100%",
        "30/30 golden questions",
    )

    # --------------------------------------------------------
    # RAGAS arithmetic summary
    # --------------------------------------------------------

    evidence_box(
        ax,
        21,
        "RAGAS Metric Mean",
        "0.9526",
        "project arithmetic summary",
    )

    # --------------------------------------------------------
    # Faithfulness
    # --------------------------------------------------------

    evidence_box(
        ax,
        40,
        "Faithfulness",
        "0.9875",
        "20-question RAGAS set",
    )

    # --------------------------------------------------------
    # Mean generation cost
    # --------------------------------------------------------

    evidence_box(
        ax,
        59,
        "Mean Gen. Cost",
        "$0.01983",
        "generation-only USD/query",
    )

    # --------------------------------------------------------
    # P95 generation cost
    # --------------------------------------------------------

    evidence_box(
        ax,
        78,
        "P95 Gen. Cost",
        "$0.02206",
        "generation-only USD/query",
    )

    # --------------------------------------------------------
    # P50 latency
    # --------------------------------------------------------

    evidence_box(
        ax,
        97,
        "P50 Latency",
        "10.945 s",
        "end-to-end benchmark",
    )

    # ========================================================
    # FOOTNOTE
    # ========================================================

    ax.text(
        118,
        0.4,
        (
            "Evidence snapshot: 30 Sep–1 Oct 2026"
        ),
        fontsize=6.5,
        ha="right",
        va="bottom",
        color=TEXT_COLOR,
    )

    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    fig.savefig(
        PNG_OUTPUT,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )

    fig.savefig(
        SVG_OUTPUT,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(
        fig
    )

    print(
        f"[OK] "
        f"{PNG_OUTPUT.relative_to(ROOT)}"
    )

    print(
        f"[OK] "
        f"{SVG_OUTPUT.relative_to(ROOT)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 72
    )

    print(
        "Yemen Opportunity Navigator"
    )

    print(
        "Architecture Diagram Generator — Final Revised"
    )

    print(
        "=" * 72
    )

    print()

    generate_architecture_diagram()

    print()

    print(
        "=" * 72
    )

    print(
        "COMPLETE"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()