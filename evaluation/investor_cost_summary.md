# Yemen Opportunity Navigator — Investor Cost Profile

**Pricing snapshot: 2026-09-30**

This report measures actual API usage from the evaluated two-pass RAG benchmark pipeline across the project's 30-question golden set.

## 1. Measurement Status

- Golden questions recorded: 30
- Successful measurements: 30
- Failed measurements: 0

## 2. Pricing Inputs

| Component | Rate used | Status |
|---|---:|---|
| Command A input | $2.5000 / 1M tokens | Verified pricing input |
| Command A output | $10.0000 / 1M tokens | Verified pricing input |
| Embed Multilingual v3.0 | Not supplied | Measured usage only |
| Rerank Multilingual v3.0 | Not supplied | Measured search units only |

No unverified Embed or Rerank price is silently inserted into this report.

## 3. Measured API Usage Distribution

| Metric | Mean | P50 | P95 | Maximum |
|---|---:|---:|---:|---:|
| Command A input tokens | 7380.53 | 7514.50 | 8246.00 | 8288.00 |
| Command A output tokens | 137.83 | 119.50 | 310.00 | 358.00 |
| Embedding input tokens | 24.33 | 24.50 | 32.00 | 34.00 |
| Rerank search units | 1.00 | 1.00 | 1.00 | 1.00 |
| Chat calls/query | 2.00 | 2.00 | 2.00 | 2.00 |
| Embed calls/query | 1.00 | 1.00 | 1.00 | 1.00 |
| Rerank calls/query | 1.00 | 1.00 | 1.00 | 1.00 |
| Latency (seconds) | 13.754 | 10.945 | 32.381 | 70.093 |

P95 uses the conservative nearest-rank method.

## 4. Generation Cost Distribution

| Metric | USD/query |
|---|---:|
| Mean | $0.01982967 |
| P50 | $0.02006375 |
| P95 | $0.02205750 |
| Maximum observed | $0.02419500 |

## 5. Full Variable API Cost

A full API cost is intentionally not calculated because verified Embed and/or Rerank rates were not supplied.

Raw measured token and search-unit usage is preserved so the report can be recalculated immediately when those rates are verified.

## 6. Cost by Language

| Language | N | Mean generation cost | P95 generation cost | Mean latency |
|---|---:|---:|---:|---:|
| ar | 15 | $0.02097017 | $0.02419500 | 17.198s |
| en | 15 | $0.01868917 | $0.02130250 | 10.311s |

## 7. Cost by Difficulty

| Difficulty | N | Mean generation cost | P95 generation cost | Mean latency |
|---|---:|---:|---:|---:|
| easy | 7 | $0.01932500 | $0.02123250 | 17.511s |
| hard | 11 | $0.02002273 | $0.02204250 | 10.974s |
| medium | 12 | $0.01994708 | $0.02419500 | 14.111s |

## 8. Monthly Volume Projections

Projection basis: **Generation-only cost**.

| Queries/month | Expected (Mean) | Conservative (P95) | Stress (Max observed) |
|---:|---:|---:|---:|
| 1,000 | $19.83 | $22.06 | $24.20 |
| 10,000 | $198.30 | $220.58 | $241.95 |
| 100,000 | $1,982.97 | $2,205.75 | $2,419.50 |
| 1,000,000 | $19,829.67 | $22,057.50 | $24,195.00 |

## 9. Benchmark Run Cost

Measured Command A generation cost for all successful benchmark queries: **$0.594890**.

## 11. Methodology Notes

- Every question is sent through the real production `YemenOpportunityRAG.ask()` path.
- Chat, Embed, and Rerank billed units are read from Cohere API responses.
- Successful measurements are cached in the CSV and are not rerun during resume.
- Failed measurements are discarded on resume and automatically attempted again.
- The script includes question-level retries in addition to retries already implemented inside the evaluated RAG benchmark pipeline.
- Latency is measured around the complete evaluated RAG benchmark request.
- Mean represents expected average cost.
- P95 represents a conservative planning case.
- Maximum observed cost represents the measured stress case.
- Hosting, database, support, domain, taxes, monitoring, and other fixed costs are intentionally modeled separately from per-query AI API COGS.
- Offline RAGAS evaluation cost is not treated as recurring production query cost.
