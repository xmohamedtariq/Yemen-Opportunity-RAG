# Cost Analysis — Yemen Opportunity Navigator

**Pricing and measurement snapshot: 30 September 2026**

## Executive Summary

Yemen Opportunity Navigator currently operates as a zero-cash-cost prototype for its core cloud stack: Cohere Trial API usage, Streamlit Community Cloud, the `streamlit.app` subdomain, Supabase Free, GitHub Free, local Chroma, and local BM25 all have a current direct cash cost of **$0/month**, provided their free-tier and trial limits are respected.

For investor planning, current cash cost and normalized production-equivalent cost must be separated. The current Cohere Trial key is free, but it is not permitted for commercial production use. The production-equivalent generation cost was therefore measured from actual billed token units across the complete 30-question golden set and priced using the official Command A production rate.

The measured Command A generation cost is:

| Metric | Cost per query |
|---|---:|
| Mean | **$0.01982967** |
| P50 | **$0.02006375** |
| P95 | **$0.02205750** |
| Maximum observed | **$0.02419500** |

The system achieved **30/30 successful cost-profile queries**. Embed and Rerank usage was also measured, but their current public PAYG numeric rates were not inserted because the current Cohere public pricing material reviewed for this analysis does not expose a self-serve numeric rate for the legacy models used by this project (`embed-multilingual-v3.0` and `rerank-multilingual-v3.0`). Their cost is therefore represented with an exact formula so that the model can be updated immediately from the Cohere production billing quote/dashboard.

---

## 1. Cost Classification

Every financial number in this document is classified as one of the following:

| Label | Meaning |
|---|---|
| **MEASURED** | Directly observed from the evaluated Yemen Opportunity Navigator benchmark path |
| **OFFICIAL** | Current published provider price or quota checked on 30 September 2026 |
| **CALCULATED** | Arithmetic derived from measured usage and/or official prices |
| **ASSUMPTION** | Planning scenario used for sensitivity analysis; not claimed as current actual spend |

This distinction is important because a $0 prototype invoice is not the same thing as the economic cost of operating the same workload commercially.

---

## 2. Current Architecture Relevant to Cost

The current public default query path passes through:

1. One Cohere `embed-multilingual-v3.0` query embedding.
2. Local Chroma vector retrieval.
3. Local BM25 keyword retrieval.
4. One Cohere `rerank-multilingual-v3.0` rerank operation.
5. One Cohere `command-a-03-2025` Chat call for grounded draft generation.
6. An optional second Command A review pass when `RAG_ENABLE_ANSWER_REVIEW=1`.
7. Streamlit Community Cloud for the application.
8. Supabase for authentication and user-related data.
9. GitHub for source control and deployment integration.

The published RAGAS, generation-cost, and latency evidence was collected with the optional review pass enabled, so those benchmark results reflect **two Chat calls per query**.

Chroma and BM25 have **no separate SaaS invoice** in the current architecture. On paid hosting they still consume RAM, CPU, and disk, so their infrastructure cost is included indirectly in hosting resource usage rather than being truly resource-free.

---

## 3. Current Cash Cost — Prototype / Demo

| Component | Current state | Current direct cash cost | Important limit |
|---|---|---:|---|
| Cohere AI | Trial key | **$0** | Trial usage is free but limited and not for commercial production |
| Streamlit hosting | Community Cloud | **$0/month** | Community/prototype environment |
| App subdomain | `*.streamlit.app` | **$0/year** | Not an independently owned domain |
| Supabase | Free | **$0/month** | 50,000 MAU, 500 MB DB, 5 GB egress, 1 GB storage |
| GitHub | Free | **$0/month** | Advanced team/enterprise controls not included |
| Chroma | Local | **$0 separate vendor fee** | Consumes host resources |
| BM25 | Local | **$0 separate vendor fee** | Consumes host resources |
| DNS | Not separately purchased | **$0** | Current Streamlit URL does not require a purchased domain |
| SSL/TLS | Included with hosted URL | **$0** | Managed by the hosting platform |
| Custom domain | Not purchased | **$0** | Optional future cost |
| RAGAS | Offline evaluation | Not recurring production COGS | Evaluation-only activity |

**Current fixed cloud cash cost: approximately $0/month.**

This does **not** include developer labor, the user's internet/electricity, taxes, legal/compliance work, customer support, marketing, payment-processing fees, or any future commercial infrastructure.

---

## 4. Cohere Trial Capacity

### 4.1 Current trial status

Cohere Trial API calls are free. Trial keys are rate limited and are not allowed for production/commercial use.

Cohere currently documents a **1,000 API-call/month** trial limit.

### 4.2 Calls consumed by one normal query

The historical cost/evaluation run measured this two-pass profile:

| API operation | Calls/query |
|---|---:|
| Embed | 1 |
| Rerank | 1 |
| Command A draft | 1 |
| Command A refinement | 1 |
| **Historical evaluated total** | **4** |

That profile implies a theoretical trial ceiling of:

`1,000 API calls / 4 calls per query = 250 complete queries/month`

The public deployment now defaults to `RAG_ENABLE_ANSWER_REVIEW=0`. A normal successful query therefore uses one Embed call, one Rerank call, and one Chat call (**3 API calls/query**), implying a simple theoretical ceiling of about **333 complete queries/month** under a 1,000-call aggregate allowance.

These are arithmetic ceilings, not guaranteed service capacity. The practical ceiling is lower because retries, testing, ingestion/re-indexing, evaluation, failed requests, provider-specific endpoint limits, and quota policy may also consume or constrain calls.

This is why the current $0 AI invoice must not be used as a commercial scaling assumption.

---

## 5. Measured 30-Question Evaluated Benchmark Usage

The final cost profile successfully completed all **30/30** golden-set questions.

### 5.1 API usage distribution

| Metric | Mean | P50 | P95 | Maximum |
|---|---:|---:|---:|---:|
| Command A input tokens | 7,380.53 | 7,514.50 | 8,246.00 | 8,288.00 |
| Command A output tokens | 137.83 | 119.50 | 310.00 | 358.00 |
| Embedding input tokens | 24.33 | 24.50 | 32.00 | 34.00 |
| Rerank search units | 1.00 | 1.00 | 1.00 | 1.00 |
| Chat calls/query | 2.00 | 2.00 | 2.00 | 2.00 |
| Embed calls/query | 1.00 | 1.00 | 1.00 | 1.00 |
| Rerank calls/query | 1.00 | 1.00 | 1.00 | 1.00 |
| Latency, seconds | 13.754 | 10.945 | 32.381 | 70.093 |

P95 uses the conservative nearest-rank method.

The 70.093-second maximum should be interpreted as an operational tail observation, not normal steady-state latency. Earlier profiling showed transient DNS/network retries, so this maximum includes resilience/retry effects rather than pure model inference alone.

### 5.2 Language split

| Language | N | Mean generation cost/query | P95 | Mean latency |
|---|---:|---:|---:|---:|
| Arabic | 15 | $0.02097017 | $0.02419500 | 17.198 s |
| English | 15 | $0.01868917 | $0.02130250 | 10.311 s |

Arabic generation was approximately **12.20% more expensive** than English on this 30-question sample:

`($0.02097017 / $0.01868917 - 1) × 100 ≈ 12.20%`

This is a measured sample characteristic, not a claim that Arabic will always cost exactly 12.20% more.

---

## 6. Official Command A Production Pricing

The production generation model is `command-a-03-2025`.

Official rate used:

| Usage | Price |
|---|---:|
| Input | **$2.50 / 1,000,000 tokens** |
| Output | **$10.00 / 1,000,000 tokens** |

### 6.1 Mean generation cost formula

Mean input:

`7,380.53 × $2.50 / 1,000,000 = $0.018451325`

Mean output:

`137.83 × $10.00 / 1,000,000 = $0.001378300`

Expected generation cost from rounded mean token counts:

`$0.018451325 + $0.001378300 = $0.019829625/query`

The row-level measured mean is **$0.01982967/query**; the tiny difference is due to rounding the displayed mean token counts.

### 6.2 Benchmark economic value

The complete 30-query benchmark had a production-equivalent Command A generation value of:

**$0.594890**

The current Trial key may make the cash invoice $0, but the benchmark's production-equivalent generation value is still useful for forecasting commercial operation.

---

## 7. Generation Cost Distribution

| Planning case | Generation cost/query | Meaning |
|---|---:|---|
| Expected | **$0.01982967** | Mean observed cost |
| Median | **$0.02006375** | P50 |
| Conservative | **$0.02205750** | P95 |
| Stress | **$0.02419500** | Maximum observed |

For budgeting, the **P95 case** is a stronger operating reserve than the mean. The maximum is useful as a measured stress case.

---

## 8. Monthly and Annual Command A Cost

### 8.1 Monthly generation cost

| Queries/month | Mean | P50 | P95 conservative | Max observed stress |
|---:|---:|---:|---:|---:|
| 1,000 | $19.83 | $20.06 | $22.06 | $24.20 |
| 10,000 | $198.30 | $200.64 | $220.58 | $241.95 |
| 100,000 | $1,982.97 | $2,006.38 | $2,205.75 | $2,419.50 |
| 1,000,000 | $19,829.67 | $20,063.75 | $22,057.50 | $24,195.00 |

### 8.2 Annual generation cost

| Queries/month | Mean annual | P95 annual | Max annual stress |
|---:|---:|---:|---:|
| 1,000 | $237.96 | $264.69 | $290.34 |
| 10,000 | $2,379.56 | $2,646.90 | $2,903.40 |
| 100,000 | $23,795.60 | $26,469.00 | $29,034.00 |
| 1,000,000 | $237,956.04 | $264,690.00 | $290,340.00 |

These are **Command A generation costs only**, not total AI COGS.

---

## 9. Embed and Rerank — Exact Cost Formula Without Invented Prices

The project uses:

- `embed-multilingual-v3.0`
- `rerank-multilingual-v3.0`

Measured usage:

- Mean embedding tokens/query = **24.33**
- P95 embedding tokens/query = **32**
- Max embedding tokens/query = **34**
- Rerank = **1 search unit/query**

Cohere documents that Embed is billed by embedded tokens and Rerank by search units. A Rerank search unit is one query with up to 100 documents, subject to Cohere's document-chunking rules.

However, the public Cohere pricing material reviewed on the pricing snapshot date does not expose a numeric self-serve PAYG rate for these legacy v3 models. Therefore no unverified dollar rate is inserted.

Define:

`E = verified Embed price in USD per 1,000,000 tokens`

`R = verified Rerank price in USD per 1,000 searches`

Then:

### Mean full AI variable cost/query

`C_mean = $0.01982967 + (24.33 × E / 1,000,000) + (1 × R / 1,000)`

### Conservative component-wise P95 formula

`C_P95 = $0.02205750 + (32 × E / 1,000,000) + (1 × R / 1,000)`

### Conservative component-wise maximum formula

`C_max = $0.02419500 + (34 × E / 1,000,000) + (1 × R / 1,000)`

These equations make the financial model immediately recalculable when the production Cohere billing quote/dashboard provides `E` and `R`.

---

## 10. Streamlit Hosting — Current Free Case

The current application is hosted on Streamlit Community Cloud.

**OFFICIAL current cost: $0/month.**

Streamlit Community Cloud deploys applications to a `streamlit.app` subdomain, so the current application URL has no separate domain registration cost.

Therefore:

`Current Streamlit hosting = $0/month`

`Current app subdomain = $0/year`

This is appropriate for the current capstone/demo deployment. A commercial-scale architecture should budget for a production host, resource monitoring, capacity, and SLA requirements separately.

---

## 11. Railway — Paid Hosting Alternative

Railway is a possible paid hosting path.

Official plans:

| Railway plan | Minimum monthly commitment |
|---|---:|
| Free | $0/month, with limited free resources |
| Hobby | **$5/month** |
| Pro | **$20/month** |
| Enterprise | Custom |

Railway's plan fee is a minimum usage commitment and counts toward resource usage.

Official resource rates:

| Resource | Rate |
|---|---:|
| RAM | **$10 / GB / month** |
| CPU | **$20 / vCPU / month** |
| Network egress | **$0.05 / GB** |
| Volume storage | **$0.15 / GB / month** |

### 11.1 Exact Railway formula

`Railway resource spend =`
`average RAM GB × $10`
`+ average vCPU × $20`
`+ outbound GB × $0.05`
`+ volume GB × $0.15`

Approximate plan invoice:

`Hobby bill ≈ max($5, resource spend)`

`Pro bill ≈ max($20, resource spend)`

### 11.2 Illustrative small-MVP case — ASSUMPTION

Assume:

- 0.50 GB average RAM
- 0.05 average vCPU
- 5 GB outbound traffic/month
- 1 GB persistent volume

Calculation:

`0.50 × $10 = $5.00 RAM`

`0.05 × $20 = $1.00 CPU`

`5 × $0.05 = $0.25 egress`

`1 × $0.15 = $0.15 storage`

`Total illustrative resource usage = $6.40/month`

Therefore:

- Hobby illustrative bill ≈ **$6.40/month**
- Pro illustrative bill ≈ **$20/month**, because usage remains below the $20 plan commitment

This $6.40 is an **ASSUMPTION**, not a measured Yemen Opportunity hosting bill. Actual Railway usage must be measured after deployment.

Railway also supports custom domains and automatically provisions free SSL certificates, so a paid SSL certificate is not required for the normal setup.

---

## 12. Supabase — Free and Paid Cases

### 12.1 Current Supabase Free

Official current quotas include:

| Free resource | Included |
|---|---:|
| Plan | **$0/month** |
| Monthly active users | **50,000** |
| Database size | **500 MB/project** |
| Egress | **5 GB** |
| Cached egress | **5 GB** |
| File storage | **1 GB** |

Free projects can pause after inactivity, so the free plan should be treated as a prototype/early-stage option rather than an investor-grade availability commitment.

### 12.2 Supabase Pro

Official current baseline:

| Pro resource | Included / price |
|---|---:|
| Base plan | **$25/month** |
| Monthly active users | **100,000 included** |
| Additional MAU | **$0.00325 / MAU** |
| Database/disk | **8 GB included**, then **$0.125/GB** |
| Egress | **250 GB included**, then **$0.09/GB** |
| Cached egress | **250 GB included**, then **$0.03/GB** |
| File storage | **100 GB included**, then **$0.0213/GB** |
| Compute credit | **$10/month**, enough for one Micro instance under the current pricing model |
| Additional default-size projects | From approximately **$10/month** each |

### 12.3 MAU cost formula

For Pro:

`Supabase MAU cost = $25 + max(0, MAU - 100,000) × $0.00325`

This excludes storage, egress, compute upgrades, add-ons, and additional projects.

Examples:

| MAU | Minimum plan logic | Approx. monthly amount before other overages |
|---:|---|---:|
| 20,000 | Free can remain within MAU quota | $0 |
| 50,000 | Free ceiling | $0 |
| 100,000 | Pro included quota | $25 |
| 150,000 | $25 + 50,000 × $0.00325 | **$187.50** |
| 200,000 | $25 + 100,000 × $0.00325 | **$350.00** |
| 500,000 | $25 + 400,000 × $0.00325 | **$1,325.00** |
| 1,000,000 | $25 + 900,000 × $0.00325 | **$2,950.00** |

### 12.4 Optional Supabase custom domain

Supabase also offers a custom-domain add-on for its project/API endpoint at approximately **$10/domain/month/project** under the current pricing structure.

This is different from buying the public website's `.com` domain and is optional.

---

## 13. Queries Are Not Users — MAU Sensitivity

Query volume must never be treated as equal to monthly active users.

### 13.1 100,000 queries/month

| Queries per active user/month | Implied MAU | Minimum Supabase MAU-plan implication |
|---:|---:|---|
| 1 | 100,000 | Pro baseline, about $25 |
| 2 | 50,000 | At Free MAU ceiling |
| 5 | 20,000 | Free MAU quota |
| 10 | 10,000 | Free MAU quota |
| 20 | 5,000 | Free MAU quota |

### 13.2 1,000,000 queries/month

| Queries per active user/month | Implied MAU | Approx. minimum Supabase plan cost before other overages |
|---:|---:|---:|
| 1 | 1,000,000 | $2,950/month |
| 2 | 500,000 | $1,325/month |
| 5 | 200,000 | $350/month |
| 10 | 100,000 | $25/month |
| 20 | 50,000 | Free MAU quota is sufficient on MAU count alone |

This table demonstrates why investor models should separately forecast:
- active users;
- queries per user;
- storage;
- bandwidth;
- AI usage.

---

## 14. GitHub Cost

### Current

GitHub Free:

**$0/month**

The Free plan supports unlimited public/private repositories for normal project use.

### Paid collaboration options

| GitHub plan | Price |
|---|---:|
| Free | $0 |
| Team | **$4/user/month** |
| Enterprise | **starts at $21/user/month** |

Examples:

`5 developers × $4 = $20/month = $240/year` on Team.

`5 developers × $21 = $105/month = $1,260/year` at the Enterprise starting rate.

GitHub Team/Enterprise is not required for the current capstone; it becomes relevant if the project needs stronger collaboration, governance, enterprise identity, or compliance controls.

---

## 15. Domain, DNS, and SSL

### 15.1 Current state

Current `streamlit.app` subdomain:

**$0/year**

No separate domain purchase is currently necessary.

### 15.2 Buying an independent `.com`

The exact price depends on:
- exact domain name;
- TLD;
- whether it is standard or premium;
- registrar;
- current registry price.

Cloudflare Registrar sells domains at registry/ICANN cost without markup. Its current official API documentation shows a **standard `.com` example** at:

- Registration: **$8.57/year**
- Renewal: **$8.57/year**

This is a **planning reference**, not a quote that a specific Yemen Opportunity domain is available at that exact price.

Monthly amortization of the example:

`$8.57 / 12 = $0.7142/month`

The exact chosen domain must be checked immediately before purchase.

### 15.3 DNS

Cloudflare Registrar/DNS can be used without a separate DNS markup for a normal configuration.

### 15.4 SSL/TLS

Cloudflare Universal SSL is available for **$0 additional cost** and automatically issues/renews publicly trusted certificates for supported configurations.

Railway also automatically provisions and renews free SSL certificates for Railway and custom domains.

Therefore a normal startup deployment does **not** need a separately purchased SSL certificate.

---

## 16. Fixed-Cost Deployment Scenarios

These scenarios exclude AI variable cost unless explicitly stated.

### Scenario A — Current Demo

| Component | Monthly |
|---|---:|
| Cohere Trial | $0 within trial limits |
| Streamlit Community Cloud | $0 |
| Supabase Free | $0 |
| GitHub Free | $0 |
| Streamlit subdomain | $0 |
| DNS/SSL | $0 |
| **Fixed cash cost** | **$0/month** |

This is a demo/validation configuration, not a commercial production architecture.

### Scenario B — Lean Paid MVP

**ASSUMPTION:** Railway Hobby + Supabase Free + standard `.com` planning reference + GitHub Free.

| Component | Monthly floor |
|---|---:|
| Railway Hobby | $5.00 |
| Supabase Free | $0 |
| GitHub Free | $0 |
| Domain amortization | $0.7142 |
| SSL | $0 |
| **Fixed floor** | **$5.7142/month** |

Annual fixed floor:

`$5 × 12 + $8.57 = $68.57/year`

Actual Railway resource use can make this higher than the $5 minimum.

### Scenario C — Production Baseline

**ASSUMPTION:** Railway Pro + Supabase Pro + standard `.com` planning reference + GitHub Free.

| Component | Monthly floor |
|---|---:|
| Railway Pro | $20.00 |
| Supabase Pro | $25.00 |
| GitHub Free | $0 |
| Domain amortization | $0.7142 |
| SSL | $0 |
| **Fixed floor** | **$45.7142/month** |

Annual fixed floor:

`$20 × 12 + $25 × 12 + $8.57 = $548.57/year`

### Optional additions

| Optional item | Increment |
|---|---:|
| Supabase custom project/API domain | +$10/month |
| GitHub Team, 5 developers | +$20/month |
| GitHub Enterprise, 5 developers | +$105/month |
| Railway usage above Pro commitment | Variable |
| Supabase storage/egress/MAU overages | Variable |

Production baseline + Supabase custom domain:

**$55.7142/month fixed floor**

Production baseline + 5-person GitHub Team:

**$65.7142/month fixed floor**

Production baseline + Supabase custom domain + 5-person GitHub Team:

**$75.7142/month fixed floor**

---

## 17. Known Production Cost Floor by Query Volume

The following combines:

- measured Command A generation cost;
- Railway Pro $20 minimum;
- Supabase Pro $25;
- standard `.com` example amortized at $8.57/year.

It **excludes Embed/Rerank PAYG dollars until their production rates are verified**, so it is a known-cost floor, not the final all-in COGS.

Fixed monthly floor:

**$45.7142/month**

### 17.1 Mean case

| Queries/month | Mean generation | Fixed floor | Known monthly cost floor | Known annual cost floor |
|---:|---:|---:|---:|---:|
| 1,000 | $19.83 | $45.71 | **$65.54** | **$786.53** |
| 10,000 | $198.30 | $45.71 | **$244.01** | **$2,928.13** |
| 100,000 | $1,982.97 | $45.71 | **$2,028.68** | **$24,344.17** |
| 1,000,000 | $19,829.67 | $45.71 | **$19,875.38** | **$238,504.61** |

### 17.2 P95 conservative case

| Queries/month | P95 generation | Fixed floor | Known monthly cost floor | Known annual cost floor |
|---:|---:|---:|---:|---:|
| 1,000 | $22.06 | $45.71 | **$67.77** | **$813.26** |
| 10,000 | $220.58 | $45.71 | **$266.29** | **$3,195.47** |
| 100,000 | $2,205.75 | $45.71 | **$2,251.46** | **$27,017.57** |
| 1,000,000 | $22,057.50 | $45.71 | **$22,103.21** | **$265,238.57** |

### 17.3 Maximum-observed stress case

| Queries/month | Max generation | Fixed floor | Known monthly cost floor | Known annual cost floor |
|---:|---:|---:|---:|---:|
| 1,000 | $24.20 | $45.71 | **$69.91** | **$838.91** |
| 10,000 | $241.95 | $45.71 | **$287.66** | **$3,451.97** |
| 100,000 | $2,419.50 | $45.71 | **$2,465.21** | **$29,582.57** |
| 1,000,000 | $24,195.00 | $45.71 | **$24,240.71** | **$290,888.57** |

Again, these are known-cost floors because the v3 Embed/Rerank PAYG dollar rates still need a verified production quote.

---

## 18. Gross-Margin Planning

Investor pricing should be derived from COGS rather than an arbitrary markup.

Formula:

`Gross Margin = (Revenue - COGS) / Revenue`

Therefore:

`Required Revenue = COGS / (1 - target gross margin)`

### 18.1 Variable-generation pricing sensitivity using P95

Using P95 generation variable cost only:

`P95 variable generation COGS = $0.02205750/query`

| Target gross margin | Minimum revenue/query before fixed costs and Embed/Rerank | Minimum revenue per 1,000 queries |
|---:|---:|---:|
| 70% | $0.073525 | $73.53 |
| 80% | $0.110288 | $110.29 |
| 85% | $0.147050 | $147.05 |
| 90% | $0.220575 | $220.58 |

This table is a sensitivity calculation, not a recommended retail price.

### 18.2 80% gross-margin floor using P95 + production fixed floor

This is still a **minimum known-cost** calculation because Embed/Rerank, support, payment fees, taxes, and labor are not yet included.

| Queries/month | Known P95 COGS floor | Revenue needed for 80% GM | Revenue/query |
|---:|---:|---:|---:|
| 1,000 | $67.77 | **$338.86** | $0.3389 |
| 10,000 | $266.29 | **$1,331.45** | $0.1331 |
| 100,000 | $2,251.46 | **$11,257.32** | $0.1126 |
| 1,000,000 | $22,103.21 | **$110,516.07** | $0.1105 |

At larger volumes, fixed infrastructure is spread across more queries and unit economics converge toward the variable AI cost.

---

## 19. Academic 5x–10x Cost Heuristic

The RAG Engineering capstone reference suggests using an approximate 5x–10x multiple of operating cost to account for development, maintenance, support, and overhead.

Using this project's **P95 generation-only** cost:

| Queries/month | 5x P95 generation | 10x P95 generation |
|---:|---:|---:|
| 1,000 | $110.29 | $220.58 |
| 10,000 | $1,102.88 | $2,205.75 |
| 100,000 | $11,028.75 | $22,057.50 |

This academic heuristic is not presented as a final commercial price because it excludes verified Embed/Rerank dollars, infrastructure, support, taxes, payment fees, and customer-specific SLA obligations.

---

## 20. Competitor Pricing Context

Competitor prices provide market context, not a direct feature-for-feature valuation.

### Mendeley

Current individual premium pricing:

| Plan | Price |
|---|---:|
| Plus | $4.99/month |
| Pro | $9.99/month |
| Max | $14.99/month |

Mendeley Pro and Max include **Ask My Library**, an AI-assisted library question-answering capability.

### Zotero

Zotero itself is free/open-source; official paid individual pricing primarily covers file storage:

| Storage | Price |
|---|---:|
| 300 MB | Free |
| 2 GB | $20/year |
| 6 GB | $60/year |
| Unlimited | $120/year |

These are not direct equivalents. Yemen Opportunity Navigator is a bilingual, domain-specific opportunity-discovery and eligibility RAG service, while Mendeley and Zotero are primarily academic research/reference-management products.

---

## 21. Enterprise / Private AI Alternative

For organizations requiring dedicated/private retrieval infrastructure, Cohere also advertises Model Vault instance pricing.

Current examples include:

| Model Vault option | Monthly rate/instance | Annual rate/instance |
|---|---:|---:|
| Embed 4 Small | $2,500 | $25,000 |
| Embed 4 Medium | $3,250 | $32,500 |
| Rerank 3.5 Medium | $3,250 | $32,500 |
| Rerank 4 Fast Medium | $3,250 | $32,500 |
| Rerank 4 Pro Medium | $3,250 | $32,500 |

These are enterprise alternatives, **not costs used by the current architecture**.

---

## 22. Cost Optimization Levers

The measured data shows that Command A generation is the dominant known variable cost. The strongest future levers are:

1. Cache repeated or near-duplicate user questions.
2. Make the second refinement pass conditional when a quality gate shows it is unnecessary.
3. Test a lower-cost generation model for simple queries and route complex queries to Command A.
4. Continue limiting the Rerank candidate set.
5. Log actual billed tokens/search units in production.
6. Batch ingestion embeddings when the knowledge base is refreshed.
7. Monitor Arabic-vs-English cost because the current sample shows higher Arabic generation cost.
8. Separate trial/evaluation traffic from customer production traffic.
9. Introduce per-user or per-plan query quotas to prevent unbounded variable COGS.
10. Set infrastructure usage caps and alerts before scaling.

Any change to the default generation path or optional review policy should be re-evaluated against the project's current RAGAS quality score before replacing the published benchmark evidence.

---

## 23. Key Investor Risks and Unknowns

The financial model is strongest when its unknowns are explicit.

| Risk / unknown | Current treatment |
|---|---|
| Embed v3 PAYG dollar rate | Exact formula retained; production rate must be verified |
| Rerank v3 PAYG dollar rate | Exact formula retained; production rate must be verified |
| Future Cohere price changes | Recalculate from measured token/search-unit data |
| Railway real RAM/CPU | Formula provided; measure after deployment |
| Supabase future MAU | Sensitivity table provided |
| Domain availability | Exact domain must be checked before purchase |
| Premium domain risk | Not assumed |
| Payment processing | Excluded until monetization platform is chosen |
| Taxes | Excluded; jurisdiction/payment-provider dependent |
| Support labor | Excluded |
| Salaries/founder time | Excluded |
| Marketing/CAC | Excluded |
| SLA/compliance | Excluded until customer requirements are known |
| Retry-related API usage | Trial ceiling and operational risk explicitly noted |

---

## 24. What Is Free Now vs. What Becomes Paid

| Component | Current | Paid/commercial path |
|---|---:|---:|
| Cohere AI | $0 Trial | PAYG production API; Command A token pricing verified, Embed/Rerank rate to verify |
| Streamlit | $0 | Railway or another commercial host if required |
| App URL | $0 `streamlit.app` | Standard `.com` planning reference ~$8.57/year; actual quote varies |
| SSL | $0 | Can remain $0 with Railway/Cloudflare standard SSL |
| DNS | $0 incremental in normal Cloudflare setup | Can remain $0 incremental |
| Supabase | $0 | Pro from $25/month + overages |
| Supabase custom API domain | Not used | +$10/month/project if desired |
| GitHub | $0 | Team $4/user/month; Enterprise starts $21/user/month |
| Chroma | $0 separate fee | Resource cost absorbed by paid hosting |
| BM25 | $0 separate fee | Resource cost absorbed by paid hosting |
| RAGAS | Evaluation only | Offline QA cost, not per-user production COGS |

---

## 25. Final Financial View

### Current prototype

**Direct fixed cloud cash cost: approximately $0/month**

This is possible because the project currently uses free/trial services.

### Commercial production

The correct production formula is:

`Monthly COGS =`

`queries × [Command A cost/query + Embed cost/query + Rerank cost/query]`

`+ hosting`

`+ Supabase`

`+ domain amortization`

`+ storage/egress overages`

`+ other production services`

For the current architecture:

`Mean AI/query =`
`$0.01982967`
`+ (24.33 × E / 1,000,000)`
`+ (R / 1,000)`

where `E` and `R` are the verified production rates for the project's exact Embed and Rerank models.

A conservative production forecast should use:

`$0.02205750/query generation P95`

plus verified Embed/Rerank rates and actual infrastructure usage.

### Most important investor conclusion

The project can be demonstrated today with approximately **$0 direct monthly infrastructure cash spend**, but a commercial business case should be valued against the measured production-equivalent AI workload rather than the free trial invoice.

The measured 30-query benchmark provides a reproducible cost baseline, and the model is structured so every remaining unknown can be replaced with an audited provider rate without changing the methodology.

---

## 26. Source and Verification Register

Pricing and quota information in this report was checked on **30 September 2026** against official provider material:

- Cohere — Command A model documentation
- Cohere — API pricing, trial/production key, billed-unit, and rate-limit documentation
- Cohere — Model Vault pricing
- Streamlit — Community Cloud deployment documentation
- Railway — Pricing, billing, resource pricing, public networking, and SSL documentation
- Supabase — Pricing and billing/usage documentation
- GitHub — Official pricing
- Cloudflare Registrar — Registrar/API pricing documentation
- Cloudflare — Universal SSL documentation
- Mendeley — Official pricing
- Zotero — Official individual storage pricing
- RAG Engineering capstone cost-analysis requirements
- `evaluation/investor_cost_profile.csv`
- `evaluation/investor_cost_summary.md`

Provider prices can change. Before presenting this document to an investor as a live financing model, update the pricing snapshot and verify any rate marked as externally variable.
