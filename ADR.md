# Architecture Decision Record

## Hybrid Multilingual Retrieval, Reranking, and Resilient Grounded Generation

**Status:** Accepted  
**Date:** 2026-10-02  
**Project:** Yemen Opportunity Navigator

## Context

Yemen Opportunity Navigator answers Arabic and English questions about opportunities using a curated source corpus while keeping answers grounded in source evidence. The validated implementation contains **49 processed source records** and **164 searchable chunks**. The architecture must support semantic matching, exact-term matching, source attribution, measurable retrieval quality, reproducible evaluation, and graceful behavior when external AI services are unavailable.

## Decision

1. Use Cohere `embed-multilingual-v3.0` for document and query embeddings.
2. Use persistent Chroma for semantic vector retrieval.
3. Use BM25 with Arabic/English normalization for lexical retrieval.
4. Fuse Vector + BM25 results using RRF to create a broader hybrid candidate set.
5. Pass **20 hybrid candidates** to Cohere `rerank-multilingual-v3.0`.
6. Use the **top 5 reranked chunks** as grounded generation context.
7. Use Command A (`command-a-03-2025`) for one grounded draft by default; enable the second draft-plus-context review only when `RAG_ENABLE_ANSWER_REVIEW=1`.
8. Build source attribution separately from answer text, then render it with the final answer.
9. Use Streamlit for the UI and Supabase for authentication/session management; cache identical public queries for **5 minutes** to reduce repeated API calls.

## Production Reliability Update

The public deployment defaults to **one Chat call per uncached normal query**.

- Monthly/trial quota exhaustion is treated as **non-retryable**.
- Only transient provider/network failures are retried.
- Vector-search failure falls back to BM25.
- Reranker failure preserves the existing hybrid/BM25 ordering.
- Generation failure returns retrieved official sources with a user notice instead of failing the search.

## Alternatives Considered

Vector-only retrieval was simpler and strong at **96.67% Recall@5**, but missed one golden question.

BM25-only retrieval preserved exact lexical matching but reached only **80.00%**.

Hybrid retrieval without reranking broadened candidate diversity but achieved **90.00%**, below vector-only performance at the final top-five level.

The accepted design therefore keeps hybrid retrieval for candidate breadth and learned reranking for final precision and recall.

## Supporting Evidence

- `docs/technical_evidence.md`
- `docs/charts/architecture_diagram.png`
- `evaluation/recall_summary.md`
- `evaluation/ragas_summary.md`
- `evaluation/investor_cost_summary.md`
- `cost_analysis.md`

## Evidence — Retrieval

| Configuration | Recall@5 |
|---|---:|
| Vector only | 96.67% (29/30) |
| BM25 only | 80.00% (24/30) |
| Hybrid + RRF | 90.00% (27/30) |
| Hybrid + Cohere Reranker | **100.00% (30/30)** |

The decisive improvement comes from reranking the broader hybrid candidate set, not from raw hybrid fusion alone. Final Recall@5 is also **100% for Arabic (15/15), English (15/15), and the hard subset (11/11)**.

## Evidence — Generation Quality

| RAGAS metric | Score |
|---|---:|
| Faithfulness | 0.9875 |
| Answer Relevancy | 0.8227 |
| Context Precision | 1.0000 |
| Context Recall | 1.0000 |

The project-level arithmetic mean across these four metric averages is **0.9526**; it is a project summary, not a separate canonical RAGAS metric.

## Operational Trade-off

The reported RAGAS and cost-profile measurements were produced with the **evaluated two-pass configuration**:

- 2 Chat calls
- 1 Embed call
- 1 Rerank call

per normal query.

Across 30/30 successful cost-profile queries:

- Mean Command A generation cost: **$0.01982967/query**
- P95 generation cost: **$0.02205750/query**
- P50 end-to-end latency: **10.945 s**
- P95 latency: **32.381 s**

**Current public default:** 1 Chat + 1 Embed + 1 Rerank for an uncached normal query. The review pass can be re-enabled to reproduce the evaluated two-pass path.

## Consequences

**Benefits:** 100% Recall@5 on the current golden set, bilingual retrieval robustness, excellent context precision/recall, high faithfulness, explicit source attribution, and graceful degradation.

**Costs:** reranking adds API usage and latency; enabling the optional review pass adds a second generation call.

**Known weakness:** Answer Relevancy at **0.8227** is the primary measured quality improvement area.

**Limitations:** results are based on 30 retrieval questions, 20 RAGAS questions, and the current 49-source/164-chunk corpus; they are not guarantees for all future queries or larger deployments.

**OCR/VLM:** not in the default ingestion path because current sources are machine-readable. Conditional OCR/VLM is planned for scanned pages, complex tables, figures, graphs, and other visual content.
