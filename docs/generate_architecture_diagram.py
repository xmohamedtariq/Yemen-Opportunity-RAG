from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
CHARTS_DIR = ROOT / 'docs' / 'charts'
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = CHARTS_DIR / 'architecture_diagram.png'
SVG_PATH = CHARTS_DIR / 'architecture_diagram.svg'

FIG_W, FIG_H = 18, 10.5
BG = '#f4f4f4'
BOX_FACE = '#f8f8f8'
BOX_EDGE = '#2f2f2f'
TEXT = '#262626'
MUTED = '#555555'
ACCENT = '#dfeee7'


def add_box(ax, x, y, w, h, title, subtitle='', fc=BOX_FACE, fontsize=10.2, title_size=12.5, lw=1.6):
    patch = FancyBboxPatch((x, y), w, h,
                           boxstyle='round,pad=0.02,rounding_size=1.1',
                           linewidth=lw, edgecolor=BOX_EDGE, facecolor=fc)
    ax.add_patch(patch)
    ax.text(x + w/2, y + h*0.62, title, ha='center', va='center',
            fontsize=title_size, fontweight='bold', color=TEXT)
    if subtitle:
        ax.text(x + w/2, y + h*0.30, subtitle, ha='center', va='center',
                fontsize=fontsize, color=MUTED)
    return (x, y, w, h)


def center_left(box):
    x, y, w, h = box
    return (x, y + h/2)


def center_right(box):
    x, y, w, h = box
    return (x + w, y + h/2)


def center_top(box):
    x, y, w, h = box
    return (x + w/2, y + h)


def center_bottom(box):
    x, y, w, h = box
    return (x + w/2, y)


def arrow(ax, start, end, text=None, text_offset=(0, 0), style='-|>', lw=1.5, mutation=12, color=BOX_EDGE, connectionstyle='arc3'):
    arr = FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=mutation,
                          linewidth=lw, color=color, connectionstyle=connectionstyle)
    ax.add_patch(arr)
    if text:
        mx = (start[0] + end[0]) / 2 + text_offset[0]
        my = (start[1] + end[1]) / 2 + text_offset[1]
        ax.text(mx, my, text, fontsize=9.0, color=MUTED, ha='center', va='center')


def generate():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 96, 'Yemen Opportunity Navigator', ha='center', va='center',
            fontsize=24, fontweight='bold', color=TEXT)
    ax.text(50, 92.5, 'Evidence-Based Retrieval-Augmented Generation Architecture', ha='center', va='center',
            fontsize=15, color=MUTED)
    ax.text(50, 89.8,
            'Public default: one grounded Chat pass. Evaluated cost/latency benchmarks used the optional two-pass path.',
            ha='center', va='center', fontsize=10.5, color=MUTED)

    # Section headings
    ax.text(1.5, 85.6, 'A. Knowledge Base / Offline Ingestion', fontsize=16, fontweight='bold', color=TEXT)
    ax.text(1.5, 59.5, 'B. Online Query Pipeline', fontsize=16, fontweight='bold', color=TEXT)
    ax.text(1.5, 13.2, 'C. Measured Evidence Snapshot', fontsize=16, fontweight='bold', color=TEXT)

    # Offline row
    y_off = 74.8
    b_sources = add_box(ax, 1.3, y_off, 11.0, 8.0, 'Official Sources', '49 processed records')
    b_fetch = add_box(ax, 14.6, y_off, 10.7, 8.0, 'Fetch + Parse', 'Official source content')
    b_clean = add_box(ax, 27.6, y_off, 11.0, 8.0, 'Clean + Chunk', 'Normalized text + metadata')
    b_chunks = add_box(ax, 40.8, y_off, 10.8, 8.0, 'Chunk Corpus', '164 searchable chunks')
    b_embed = add_box(ax, 54.0, y_off, 10.6, 8.0, 'Embeddings', 'embed-multilingual-v3.0')
    b_chroma = add_box(ax, 67.1, y_off, 11.5, 8.0, 'Chroma', 'Persistent vector store')
    b_bm25 = add_box(ax, 41.2, 62.9, 12.2, 7.2, 'BM25 Index', 'Arabic + English lexical index')

    for s, e in [(b_sources, b_fetch), (b_fetch, b_clean), (b_clean, b_chunks), (b_chunks, b_embed), (b_embed, b_chroma)]:
        arrow(ax, center_right(s), center_left(e))
    arrow(ax, center_bottom(b_chunks), center_top(b_bm25), text='same chunk corpus', text_offset=(0, 1.3), mutation=10)

    # Online pipeline row 1
    b_user = add_box(ax, 1.3, 46.8, 9.6, 8.0, 'User', 'Arabic / English query')
    b_ui = add_box(ax, 12.9, 46.8, 11.7, 8.0, 'Streamlit UI', 'Query + answer interface')
    b_query = add_box(ax, 26.0, 46.8, 10.0, 8.0, 'Query', 'Language detected')
    b_qembed = add_box(ax, 38.0, 46.8, 12.0, 8.0, 'Query Embedding', 'input_type = search_query')
    b_vector = add_box(ax, 54.3, 46.8, 11.0, 8.0, 'Vector Search', 'Chroma similarity search')
    b_auth = add_box(ax, 12.9, 36.4, 11.7, 6.8, 'Supabase Auth', 'Sign up / login / session')

    arrow(ax, center_right(b_user), center_left(b_ui))
    arrow(ax, center_right(b_ui), center_left(b_query))
    arrow(ax, center_bottom(b_ui), center_top(b_auth), text='authentication', text_offset=(0, 0.5), mutation=10)
    arrow(ax, center_right(b_query), center_left(b_qembed))
    arrow(ax, center_right(b_qembed), center_left(b_vector))
    arrow(ax, (72.6, 74.8), (59.8, 54.9), text='persistent vectors', text_offset=(1.7, 0.4), mutation=10)
    arrow(ax, center_bottom(b_bm25), (44.0, 43.2), text='lexical index', text_offset=(4.5, 0.8), mutation=10)

    # Online pipeline row 2
    b_bm25s = add_box(ax, 39.0, 36.4, 12.0, 6.8, 'BM25 Search', 'Lexical keyword retrieval')
    b_hybrid = add_box(ax, 54.3, 36.4, 11.0, 6.8, 'Hybrid + RRF', 'Merge ranked candidates')
    b_candidates = add_box(ax, 68.7, 36.4, 10.5, 6.8, '20 Candidates', 'Hybrid candidate set')
    b_rerank = add_box(ax, 82.0, 36.4, 12.5, 6.8, 'Cohere Reranker', 'rerank-multilingual-v3.0')

    arrow(ax, center_bottom(b_qembed), center_top(b_bm25s), text='raw query text', text_offset=(-4.0, 0.3), mutation=10)
    arrow(ax, center_bottom(b_vector), center_top(b_hybrid), mutation=10)
    arrow(ax, center_right(b_bm25s), center_left(b_hybrid))
    arrow(ax, center_right(b_hybrid), center_left(b_candidates))
    arrow(ax, center_right(b_candidates), center_left(b_rerank))

    # Generation / output row
    b_top5 = add_box(ax, 84.0, 25.0, 8.6, 6.6, 'Top 5', 'Evidence chunks')
    b_context = add_box(ax, 44.0, 18.0, 12.2, 7.0, 'Context Builder', 'Chunk text + metadata')
    b_cmd1 = add_box(ax, 58.0, 18.0, 10.8, 7.0, 'Command A', 'Grounded draft')
    b_review = add_box(ax, 70.5, 18.0, 11.2, 7.0, 'Review Pass', 'Optional • env enabled', fc=ACCENT)
    b_cleanup = add_box(ax, 70.5, 8.4, 11.2, 7.0, 'Answer Cleanup', 'Public-safe formatting')
    b_sourcebuilder = add_box(ax, 83.2, 15.3, 11.4, 7.2, 'Source Builder', 'Source attribution metadata', fontsize=9.4)
    b_final = add_box(ax, 83.2, 7.6, 12.8, 7.2, 'Answer + Sources', 'UI response + source cards', fontsize=9.4)

    arrow(ax, center_bottom(b_rerank), center_top(b_top5), mutation=10)
    arrow(ax, center_left(b_top5), (56.3, 24.8), text='top-5 evidence', text_offset=(-1.5, 0.9), mutation=10)
    arrow(ax, center_right(b_context), center_left(b_cmd1))
    arrow(ax, center_right(b_cmd1), center_left(b_review))
    arrow(ax, center_bottom(b_review), center_top(b_cleanup), mutation=10)
    arrow(ax, center_bottom(b_top5), center_top(b_sourcebuilder), mutation=10)
    arrow(ax, center_bottom(b_sourcebuilder), center_top(b_final), mutation=10)
    arrow(ax, center_right(b_cleanup), center_left(b_final))
    arrow(ax, (68.8, 21.4), (70.4, 12.0), text='default if review disabled', text_offset=(-1.4, -0.4), mutation=10, connectionstyle='arc3,rad=-0.15')

    # Reliability note
    ax.text(49.5, 13.0, 'Graceful degradation: Vector failure → BM25  •  Reranker failure → keep hybrid order',
            ha='center', va='center', fontsize=9.0, color=MUTED)
    ax.text(49.5, 11.2, 'Generation failure or quota exhaustion → return official sources with a user notice',
            ha='center', va='center', fontsize=9.0, color=MUTED)

    # Metrics row
    metric_boxes = [
        ('Recall@5', '100%\n30/30 golden questions'),
        ('RAGAS Mean', '0.9526\nproject arithmetic summary'),
        ('Faithfulness', '0.9875\n20-question RAGAS set'),
        ('Mean Gen. Cost', '$0.01983\ngeneration-only USD/query'),
        ('P95 Gen. Cost', '$0.02206\ngeneration-only USD/query'),
        ('P50 Latency', '10.945 s\nend-to-end benchmark'),
    ]
    x = 1.2
    for title, subtitle in metric_boxes:
        add_box(ax, x, 3.2, 14.6, 6.0, title, subtitle, fc='#fbfbfb', fontsize=8.7, title_size=11.3, lw=1.4)
        x += 15.95

    ax.text(96, 0.8,
            'Evidence snapshot: 30 Sep–1 Oct 2026',
            ha='right', va='bottom', fontsize=8.8, color=MUTED)

    plt.tight_layout(pad=0.5)
    fig.savefig(PNG_PATH, dpi=220, facecolor=BG, bbox_inches='tight')
    fig.savefig(SVG_PATH, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(PNG_PATH)
    print(SVG_PATH)


if __name__ == '__main__':
    generate()
