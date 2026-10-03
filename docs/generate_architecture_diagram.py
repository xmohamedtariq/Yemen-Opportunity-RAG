
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
CHARTS_DIR = ROOT / 'docs' / 'charts'
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = CHARTS_DIR / 'architecture_diagram.png'
SVG_PATH = CHARTS_DIR / 'architecture_diagram.svg'

W, H = 188, 120
BG = '#f6f7f6'
SECTION = '#eef2ef'
BOX = '#ffffff'
METRIC = '#fbfcfb'
ACCENT = '#e3f1e7'
EDGE = '#2a2a2a'
TEXT = '#202427'
SUBT = '#61686d'
LIGHT = '#d0d7d2'


def panel(ax, x, y, w, h, title):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=1.2',
                       linewidth=1.0, edgecolor=LIGHT, facecolor=SECTION, zorder=0)
    ax.add_patch(p)
    ax.text(x + 2.2, y + h - 3.0, title, ha='left', va='center', fontsize=16, fontweight='bold', color=TEXT)


def box(ax, x, y, w, h, title, subtitle='', fc=BOX, tsize=11.0, ssize=8.5):
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=1.0',
                       linewidth=1.2, edgecolor=EDGE, facecolor=fc, zorder=2)
    ax.add_patch(b)
    ax.text(x + w/2, y + h*0.63, title, ha='center', va='center', fontsize=tsize, fontweight='bold', color=TEXT)
    if subtitle:
        ax.text(x + w/2, y + h*0.28, subtitle, ha='center', va='center', fontsize=ssize, color=SUBT)
    return (x, y, w, h)


def left(b):
    x, y, w, h = b
    return x, y + h/2


def right(b):
    x, y, w, h = b
    return x + w, y + h/2


def top(b):
    x, y, w, h = b
    return x + w/2, y + h


def bottom(b):
    x, y, w, h = b
    return x + w/2, y


def arrow(ax, p1, p2, rad=0.0, lw=1.25, ms=10):
    a = FancyArrowPatch(p1, p2, arrowstyle='-|>', mutation_scale=ms,
                        linewidth=lw, color=EDGE, connectionstyle=f'arc3,rad={rad}', zorder=1)
    ax.add_patch(a)


def note(ax, x, y, s, ha='center', size=8.1):
    ax.text(x, y, s, ha=ha, va='center', fontsize=size, color=SUBT)


def generate():
    fig, ax = plt.subplots(figsize=(20, 13), dpi=220)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')

    ax.text(W/2, 114.5, 'Yemen Opportunity Navigator', ha='center', va='center', fontsize=24, fontweight='bold', color=TEXT)
    ax.text(W/2, 111.0, 'Professional RAG System Architecture', ha='center', va='center', fontsize=14.5, color=SUBT)
    ax.text(W/2, 108.4,
            'Public app uses single-pass grounded answering. Benchmark charts reflect the optional two-pass evaluation path.',
            ha='center', va='center', fontsize=9.3, color=SUBT)

    panel(ax, 3, 75, 182, 22, 'A. Knowledge Base / Offline Ingestion')
    panel(ax, 3, 23, 182, 48, 'B. Online Query Pipeline')
    panel(ax, 3, 3, 182, 16, 'C. Measured Evidence Snapshot')

    # A. Ingestion
    yA = 82.0
    wA, hA, gapA = 19, 7.8, 2.5
    xs = [5 + i * (wA + gapA) for i in range(6)]
    A1 = box(ax, xs[0], yA, wA, hA, 'Official Sources', '49 processed records')
    A2 = box(ax, xs[1], yA, wA, hA, 'Fetch + Parse', 'Official source content')
    A3 = box(ax, xs[2], yA, wA, hA, 'Clean + Chunk', 'Normalized text + metadata')
    A4 = box(ax, xs[3], yA, wA, hA, 'Chunk Corpus', '164 searchable chunks')
    A5 = box(ax, xs[4], yA, wA, hA, 'Embeddings', 'embed-multilingual-v3.0')
    A6 = box(ax, xs[5], yA, wA, hA, 'Chroma', 'Persistent vector store')
    A7 = box(ax, xs[3] + 2.5, 76.8, 15.6, 6.7, 'BM25 Index', 'Arabic + English lexical index')

    for s, e in [(A1, A2), (A2, A3), (A3, A4), (A4, A5), (A5, A6)]:
        arrow(ax, right(s), left(e))
    arrow(ax, bottom(A4), top(A7))

    # B. Query and auth
    User = box(ax, 7, 57.8, 15.0, 7.5, 'User', 'Arabic / English query')
    UI = box(ax, 25.0, 57.8, 19.0, 7.5, 'Streamlit UI', 'Search + answer interface')
    Query = box(ax, 48.0, 57.8, 16.0, 7.5, 'Query', 'Language detected')
    Auth = box(ax, 25.0, 48.5, 19.0, 6.5, 'Supabase Auth', 'Sign up / login / session')
    arrow(ax, right(User), left(UI))
    arrow(ax, right(UI), left(Query))
    arrow(ax, bottom(UI), top(Auth))

    # Retrieval
    Embed = box(ax, 70.0, 57.8, 19.0, 7.5, 'Query Embedding', 'input_type = search_query')
    Vector = box(ax, 96.0, 57.8, 19.0, 7.5, 'Vector Search', 'Chroma similarity search')
    BM25 = box(ax, 70.0, 47.0, 19.0, 7.0, 'BM25 Search', 'Lexical keyword retrieval')
    Hybrid = box(ax, 96.0, 47.0, 19.0, 7.0, 'Hybrid + RRF', 'Merge ranked candidates')
    Cand = box(ax, 120.0, 47.0, 16.0, 7.0, '20 Candidates', 'Hybrid candidate set')
    Rerank = box(ax, 140.0, 47.0, 19.0, 7.0, 'Cohere Reranker', 'rerank-multilingual-v3.0')
    Top5 = box(ax, 146.0, 36.5, 12.5, 6.5, 'Top 5', 'Evidence chunks')

    arrow(ax, right(Query), left(Embed))
    arrow(ax, right(Embed), left(Vector))
    arrow(ax, bottom(Embed), top(BM25))
    arrow(ax, bottom(Vector), top(Hybrid))
    arrow(ax, right(BM25), left(Hybrid))
    arrow(ax, right(Hybrid), left(Cand))
    arrow(ax, right(Cand), left(Rerank))
    arrow(ax, bottom(Rerank), top(Top5))

    arrow(ax, (top(A6)[0], 82.0), (105.5, 65.5))
    arrow(ax, (top(A7)[0], 76.8), (79.5, 54.0))

    # Generation + sources
    Context = box(ax, 112.0, 28.0, 16.5, 7.0, 'Context Builder', 'Chunk text + metadata')
    Source = box(ax, 132.0, 28.0, 16.5, 7.0, 'Source Builder', 'Attribution metadata')
    Draft = box(ax, 90.5, 17.2, 15.0, 7.0, 'Command A', 'Grounded draft')
    Review = box(ax, 109.0, 17.2, 15.5, 7.0, 'Review Pass', 'Optional • env enabled', fc=ACCENT)
    Cleanup = box(ax, 128.0, 17.2, 16.0, 7.0, 'Answer Cleanup', 'Public-safe formatting')
    Answer = box(ax, 148.0, 17.2, 18.5, 7.0, 'Answer + Sources', 'UI response + source cards')

    arrow(ax, bottom(Top5), top(Context), rad=0.0)
    arrow(ax, bottom(Top5), top(Source), rad=0.0)
    arrow(ax, left(Context), right(Draft))
    # main generation path
    arrow(ax, left(Draft), right(Review))
    arrow(ax, left(Review), right(Cleanup))
    arrow(ax, left(Cleanup), right(Answer))
    arrow(ax, bottom(Source), top(Answer))

    # metrics
    metrics = [
        ('Recall@5', '100%\n30/30 golden questions'),
        ('RAGAS Mean', '0.9526\nproject arithmetic summary'),
        ('Faithfulness', '0.9875\n20-question RAGAS set'),
        ('Mean Gen. Cost', '$0.01983\ngeneration-only USD/query'),
        ('P95 Gen. Cost', '$0.02206\ngeneration-only USD/query'),
        ('P50 Latency', '10.945 s\nend-to-end benchmark'),
    ]
    x = 7.0
    for title, subtitle in metrics:
        box(ax, x, 6.6, 24.0, 5.8, title, subtitle, fc=METRIC, tsize=10.3, ssize=8.1)
        x += 24.0 + 2.0

    ax.text(182.5, 4.1, 'Evidence snapshot: 30 Sep–1 Oct 2026', ha='right', va='bottom', fontsize=8.1, color=SUBT)

    plt.tight_layout(pad=0.7)
    fig.savefig(PNG_PATH, dpi=220, facecolor=BG, bbox_inches='tight')
    fig.savefig(SVG_PATH, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(PNG_PATH)
    print(SVG_PATH)


if __name__ == '__main__':
    generate()
