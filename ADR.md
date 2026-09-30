# ADR-001 — Hybrid Multilingual Retrieval, Reranking, and Two-Pass Grounded Generation

**Status:** Accepted
**Date:** 2026-10-01
**Project:** Yemen Opportunity Navigator

## Context

Yemen Opportunity Navigator must answer Arabic and English questions about opportunities using a curated source corpus while keeping answers grounded in source evidence. The current validated implementation contains **49 processed source records** and **164 searchable chunks**. The architecture must support semantic matching, exact-term matching, source attribution, measurable retrieval quality, and reproducible evaluation.

## Decision

The production RAG path will use:

1. **Cohere `embed-multilingual-v3.0`** for document and query embeddings.
2. **Persistent Chroma** for semantic vector retrieval.
3. **BM25** with Arabic/English normalization for lexical retrieval.
4. **Hybrid Vector + BM25 fusion using RRF** to form a broader candidate set.
5. **20 hybrid candidates** passed to **Cohere `rerank-multilingual-v3.0`**.
6. **Top 5 reranked chunks** used as the grounded generation context.
7. **Command A (`command-a-03-2025`) in two passes**: grounded draft, then draft-plus-context review.
8. **Source attribution built separately from answer text**, then rendered with the final answer.
9. **Streamlit** as the current UI and **Supabase** for authentication/session management.

## Evidence

### Retrieval

| Configuration | Recall@5 |
|---|---:|
| Vector only | 96.67% (29/30) |
| BM25 only | 80.00% (24/30) |
| Hybrid + RRF | 90.00% (27/30) |
| **Hybrid + Cohere Reranker** | **100.00% (30/30)** |

The decisive improvement comes from **reranking the broader hybrid candidate set**, not from raw hybrid fusion alone. Final Recall@5 is also 100% for Arabic (15/15), English (15/15), and the hard subset (11/11).

### Generation quality

| RAGAS metric | Score |
|---|---:|
| Faithfulness | 0.9875 |
| Answer Relevancy | 0.8227 |
| Context Precision | 1.0000 |
| Context Recall | 1.0000 |

The project-level arithmetic mean across these four metric averages is **0.9526**; it is a project summary, not a separate canonical RAGAS metric.

### Operational trade-off

The measured production path uses **2 Chat calls + 1 Embed call + 1 Rerank call per normal query**. Across 30/30 successful cost-profile queries:

- Mean Command A generation cost: **$0.01982967/query**
- P95 generation cost: **$0.02205750/query**
- P50 end-to-end latency: **10.945 s**
- P95 latency: **32.381 s**

## Alternatives Considered

**Vector-only retrieval** was simpler and strong at 96.67% Recall@5, but missed one golden question.
**BM25-only retrieval** preserved exact lexical matching but reached only 80.00%.
**Hybrid without reranking** broadened candidate diversity but achieved 90.00%, below vector-only performance at the final top-five level.
Therefore, the accepted design keeps hybrid retrieval for candidate breadth and uses learned reranking to recover final precision and recall.

## Consequences

**Benefits:** 100% Recall@5 on the current golden set, bilingual retrieval robustness, excellent context precision/recall, high faithfulness, and explicit source attribution.

**Costs:** extra API usage and latency from reranking and the second generation pass.

**Known weakness:** Answer Relevancy at **0.8227** is the primary measured quality improvement area.

**Limitations:** results are based on 30 retrieval questions, 20 RAGAS questions, and the current 49-source/164-chunk corpus. They are not guarantees for all future queries or larger-scale deployments.

## Supporting Evidence

- [`docs/technical_evidence.md`](docs/technical_evidence.md)
- [`docs/charts/architecture_diagram.png`](docs/charts/architecture_diagram.png)
- [`evaluation/recall_summary.md`](evaluation/recall_summary.md)
- [`evaluation/ragas_summary.md`](evaluation/ragas_summary.md)
- [`evaluation/investor_cost_summary.md`](evaluation/investor_cost_summary.md)
- [`cost_analysis.md`](cost_analysis.md)
