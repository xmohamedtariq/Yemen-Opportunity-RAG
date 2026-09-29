# Yemen Opportunity RAG — Recall@5 Evaluation

Total evaluated questions: 30

## Overall Results

| Retrieval Method | Hits | Recall@5 |
|---|---:|---:|
| Vector Search | 29/30 | 96.67% |
| BM25 | 24/30 | 80.00% |
| Hybrid (Vector + BM25 + RRF) | 27/30 | 90.00% |
| Hybrid + Cohere Reranker | 30/30 | 100.00% |

## Improvements

- Hybrid vs Vector: -6.67 percentage points
- Reranker vs Hybrid: +10.00 percentage points
- Final pipeline vs Vector: +3.33 percentage points

## Final Pipeline by Language

| Language | Hits | Recall@5 |
|---|---:|---:|
| ar | 15/15 | 100.00% |
| en | 15/15 | 100.00% |

## Final Pipeline by Difficulty

| Difficulty | Hits | Recall@5 |
|---|---:|---:|
| easy | 7/7 | 100.00% |
| medium | 12/12 | 100.00% |
| hard | 11/11 | 100.00% |

## Questions Missed by Final Pipeline

None. All gold passages were retrieved in the top 5.

## Evaluation Definition

Recall@5 is measured at the query level. A question counts as a hit when its required gold chunk is present among the top five retrieved chunks. For questions with multiple required gold chunks, all listed gold chunks must be present in the top five.