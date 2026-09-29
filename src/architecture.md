# Yemen Opportunity RAG — Architecture

## 1. Project Overview

Yemen Opportunity RAG is a bilingual retrieval-augmented generation
system designed to help Yemeni youth discover trusted scholarships,
fellowships, internships, training programs, competitions, grants,
and technology opportunities.

The system retrieves information from official and high-quality
sources and is designed to provide answers with traceable source
metadata and URLs.

---

## 2. Corpus

The source collection initially contained 50 candidate opportunities.

After automated fetching, parsing, quality auditing, source replacement,
and manual review, 49 usable sources were included in the final corpus.

The corpus includes official sources from governments, universities,
international organizations, development institutions, and established
opportunity providers.

Source metadata includes:

- Source ID
- Title
- Provider
- Category
- URL
- Last verification date

One source was excluded because it could not be retrieved reliably
after repeated access failures.

---

## 3. Ingestion Pipeline

The ingestion pipeline follows these stages:

1. Load source metadata from `sources.csv`
2. Download source HTML or PDF
3. Store raw content
4. Parse useful text
5. Clean extracted text
6. Run source-quality auditing
7. Split validated documents into chunks
8. Run chunk-quality auditing
9. Generate embeddings
10. Store vectors and metadata in Chroma

The pipeline preserves source metadata so retrieved chunks can always
be traced back to their original source.

---

## 4. Parsing

HTML documents are parsed using BeautifulSoup with the lxml parser.

The parser removes non-content elements such as:

- script
- style
- noscript
- svg
- iframe
- button

The parser intentionally preserves HTML `<form>` elements because
some Microsoft SharePoint websites place their actual page content
inside forms.

Additional SharePoint-specific extraction is used for
`.ms-rtestate-field` content.

PDF parsing support is also included using pypdf when PDF sources
are encountered.

---

## 5. Chunking Strategy

### Strategy

Recursive text splitting using:

`RecursiveCharacterTextSplitter`

### Configuration

- Chunk size: 600 tokens
- Chunk overlap: 90 tokens
- Overlap percentage: 15%
- Token encoding: `cl100k_base`

### Rationale

A 600-token chunk size provides enough context to preserve complete
descriptions, eligibility requirements, benefits, and application
details while remaining sufficiently focused for retrieval.

A 15% overlap reduces the chance that important information is lost
when content crosses chunk boundaries.

Recursive splitting was selected because it attempts to preserve
natural text boundaries before falling back to smaller separators.

### Result

- Validated sources: 49
- Total chunks: 164
- Empty chunks: 0
- Very short chunks: 0
- Oversized chunks: 0
- Valid chunks: 164

---

## 6. Embedding Model

### Selected model

`embed-multilingual-v3.0`

Provider: Cohere

### Rationale

The system is intended to support Arabic and English queries while
many of the source documents are written primarily in English.

A multilingual embedding model is therefore important for
cross-lingual semantic retrieval.

For example, an Arabic query about:

"منح تغطي تكاليف السفر"

should still be able to retrieve an English source discussing:

"airfare" or "travel allowance".

Cohere multilingual embeddings were successfully tested through the
API before building the vector database.

OpenAI `text-embedding-3-small` was considered as an alternative.
The API credential was successfully detected, but evaluation could
not be completed because the OpenAI API account had no remaining
credits. Therefore, no unsupported performance comparison between
the two models is claimed.

---

## 7. Vector Database

### Selected database

Chroma

### Collection

`yemen_opportunities`

### Distance metric

Cosine similarity

### Rationale

Chroma was selected because:

- The current corpus is relatively small.
- It supports persistent local storage.
- It integrates well with Python and LangChain.
- It supports metadata filtering.
- It is suitable for rapid RAG prototyping.
- It can later be replaced by a production vector database if scale
  requirements increase.

The database is stored locally under:

`data/chroma/`

---

## 8. Vector Store Result

The final vector database contains:

- 49 source documents
- 164 text chunks
- 164 vector embeddings
- Source metadata for every chunk

Each indexed chunk contains metadata including:

- chunk_id
- source_id
- chunk_index
- title
- provider
- category
- URL

---

## 9. Current Retrieval Architecture

Current semantic retrieval pipeline:

User Query
    ↓
Cohere multilingual query embedding
    ↓
Chroma cosine similarity search
    ↓
Top-K relevant chunks
    ↓
Source metadata and URLs

---

## 10. Next Retrieval Architecture

The next stage will extend the retrieval system to:

User Query
    ↓
Query Processing
    ↓
Vector Search + BM25
    ↓
Reciprocal Rank Fusion
    ↓
Reranking
    ↓
Top relevant chunks
    ↓
Grounded LLM generation
    ↓
Answer with citations

Retrieval quality will be evaluated using a manually prepared
30-question golden dataset and Recall@5.