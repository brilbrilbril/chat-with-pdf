# Technical Documentation

## Architecture

The system follows **Clean Architecture** with strict dependency rules - outer layers depend on inner layers, never the reverse. Infrastructure and framework concerns are isolated from business logic.

### Dependency Rule

- **Domain** has zero external imports — only Python stdlib
- **Use Cases** depend only on domain interfaces (ports), never on concrete implementations
- **Infrastructure** implements domain interfaces and may import third-party libraries
- **API** wires everything together via FastAPI's dependency injection

### Project Structure (backend)

```
src/
├── domain/
│   ├── entities/          # Document, Chunk, ChunkSource, Message, ChatSession
│   └── interfaces/        # DocumentRepository, EmbeddingService, LLMService, IBaseExtractor
├── use_cases/
│   ├── ingest_document.py # Extract → embed → persist pipeline
│   └── chat.py            # Agentic chat loop with tool dispatch
├── infrastructure/
│   ├── extractors/        # Per-format extractors + router + chunker
│   ├── db/                # PostgresDocumentRepository
│   ├── embedding/         # OpenAI embedding service
│   ├── llm/               # OpenAI LLM service
│   └── monitoring/        # LangSmith wrapper
└── api/
    ├── routes/            # Document and chat endpoints
    ├── schemas/           # Pydantic request/response models
___ core/                  # utils
```

---

## Ingestion Pipeline

```
POST /documents/upload
        │
        ▼
  Format detection (by file extension)
        │
        ▼
  Extractor Router
        │
        ├── .pdf  → PDFExtractor   (structure-aware)
        ├── .docx → DOCXExtractor  (structure-aware)
        ├── .pptx → PPTXExtractor  (recursive, per slide)
        ├── .xlsx → XLSXExtractor  (row batching)
        ├── .csv  → CSVExtractor   (row batching)
        └── .txt  → TXTExtractor   (recursive)
        │
        ▼
  Raw chunks with source metadata
  (page_number | slide_number | sheet_name + row_range | chunk_index)
        │
        ▼
  Embed in batches of 20 (OpenAI API)
        │
        ▼
  Single atomic transaction
  INSERT documents + INSERT chunks + UPDATE chunk_count
        │
        ▼
  pgvector stores embeddings as VECTOR(1536)
```

File extraction runs in a thread pool via `asyncio.to_thread` so the event loop stays free for concurrent requests during the blocking file parse step.

---

## Chunking Strategy

Different document types warrant different chunking strategies. A one-size-fits-all approach produces either too-small fragments or chunks that cut across semantic boundaries.

### Structure-Aware (PDF, DOCX)

Segments the document into `(heading, body)` pairs first, then chunks each section independently. The heading is re-injected as a prefix into every sub-chunk, so retrieved chunks always carry section context.

**Heading detection for PDF** (heuristic, no font metadata):
- Short lines (≤ 12 words) that don't end with sentence punctuation
- ALL CAPS lines — common in SOPs and regulations
- Title Case short lines — common in reports
- Numbered patterns: `1.`, `1.1`, `BAB I`, `PASAL 3` (Indonesian legal docs)
- Academic patterns: `1 Introduction`, `2.1 Related Work`, `Abstract`, `Conclusion`

**Heading detection for DOCX**:
Uses `paragraph.style.name` directly — `Heading 1`, `Heading 2`, `Title`, etc. More reliable than heuristics since it reads the actual document structure.

**Section chunking**:
- If heading + body fits within `chunk_size` → emit as one chunk
- If body is too large → split body recursively, re-inject heading prefix into each piece

### Recursive Splitting (PPTX, TXT)

Tries separators in priority order: `\n\n` → sentence boundary → `\n` → words. Never cuts mid-sentence if a higher-priority separator is available. Word-count splitting is the last resort only.

PPTX splits per slide first (natural boundary), then applies recursive splitting within each slide's text.

### Row Batching (XLSX, CSV)

Rows are grouped in batches (XLSX: 30 rows, CSV: 40 rows) with the header row prepended to every chunk. This ensures the embedding captures column semantics, not just naked values.

**Note**: The better approach is like text-to-SQL, but since it's only for demo, so I didnt over-engineer it into text-to-sql

```
Sheet: Sales Q1 | Rows 2–31
Date       | Invoice ID | Amount   | Region
2024-01-15 | INV-001    | 5000000  | Jakarta
...
```

Source metadata: `sheet_name` + `row_start` + `row_end` for exact traceability.

### Noise Filtering (PDF)

PDF extraction is noisy. Chunks are filtered before indexing if they:
- Are below 30 words (stray labels, headers, page numbers)
- Consist of more than 30% pipe characters (ASCII figure/table renderings)
- Contain more than 10% `(cid:N)` tokens (garbled font encoding artifacts)

### Small Chunk Merging

After splitting, chunks below `MIN_CHUNK_WORDS` (30) are merged forward into the next chunk rather than dropped. This prevents semantic content from being lost while still enforcing a minimum useful chunk size.

---

## Retrieval (RAG)

### Vector Search

Chunks are stored as `VECTOR(1536)` in pgvector. Similarity search uses cosine distance:

```sql
SELECT *, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
FROM chunks
JOIN documents ON chunks.document_id = documents.id
WHERE documents.session_id = :session_id
ORDER BY embedding <=> CAST(:query_embedding AS vector)
LIMIT :top_k
```

An IVFFlat index (`lists = 100`) is used for approximate nearest neighbor search, trading a small accuracy loss for significant query speed improvement at scale.

### Session Isolation

Every document upload is tagged with a `session_id`. Vector search filters by `session_id` via a JOIN on the documents table, so two sessions never see each other's documents. Session data is automatically purged after 24 hours by a background scheduler.

### Agentic Chat Loop

The LLM is given a single tool: `search_documents(query, top_k)`. On each user message:

1. LLM decides whether to call the tool (it always should for document questions)
2. Tool executes vector search, returns formatted chunks with citations
3. LLM receives tool result and generates a cited answer
4. If LLM calls the tool again, the loop repeats (max 3 iterations to prevent infinite loops)
5. Final answer is streamed back via SSE

The system prompt instructs the model to call `search_documents` once and synthesize immediately — preventing the loop behavior common in smaller models.

### Conversation History

History is stored in-memory per session as a list of `Message` objects. On each turn, the full history is included in the OpenAI messages array. When total token count approaches the 64k budget, oldest messages are dropped (sliding window truncation) while preserving at least the last 2 turns.

---

## Embedding Model Selection

**Model: `text-embedding-3-small` (OpenAI)**

| Dimension | Cost | Performance |
|-----------|------|-------------|
| 1536 | $0.02 / 1M tokens | Strong multilingual, including Indonesian |

**Why not a local embedding model?**

Running a local embedding model (e.g. `nomic-embed-text`, `bge-m3`) on consumer hardware (RTX 4060, 8GB VRAM) is feasible but introduces operational complexity:

- VRAM must be shared between the embedding model and LLM, leaving insufficient headroom for a capable LLM
- Inference throughput on a single GPU is a bottleneck during bulk ingestion
- Maintaining a local inference server adds a failure surface

For the document domain (SOPs, regulations, reports — primarily Indonesian), `text-embedding-3-small` has strong multilingual coverage and outperforms many open models on semantic similarity benchmarks. The cost is negligible at this scale.

**Tradeoff**: API dependency and latency (~50–200ms per batch). Mitigated by batching 20 chunks per API call during ingestion.

---

## LLM Selection

**Model: `gpt-4o-mini` (OpenAI)**

| Context window | Cost (input) | Cost (output) | Tool call support |
|---------------|-------------|--------------|------------------|
| 128k tokens | $0.15 / 1M | $0.60 / 1M | Native |

**Why not a local LLM?**

During development, local inference was tested with `Qwen3-4B` via llama-server. The experience surfaced several issues that make local LLMs a poor fit for production in this use case:

- **Tool call reliability**: Smaller models inconsistently follow tool call instructions. `Qwen3-4B` frequently skipped the `search_documents` call on ambiguous queries or looped on tool calls without synthesizing an answer.
- **Citation quality**: Smaller models tend to hallucinate source attributions or ignore retrieved context when the question is phrased vaguely.
- **GPU cost**: Renting a GPU instance (e.g. A10G on AWS) costs ~$0.75–1.50/hour. At low-to-moderate traffic, this far exceeds OpenAI API costs.
- **Operational overhead**: Running llama-server, managing model files, monitoring inference health adds significant complexity for a production system.

`gpt-4o-mini` reliably follows tool call instructions, produces well-structured cited answers, and is cost-effective at scale. At $0.60/1M output tokens, a 500-token answer costs $0.0003.

**Tradeoff**: API dependency, data leaves the device (relevant for sensitive documents), latency subject to OpenAI availability. For air-gapped or highly sensitive deployments, a self-hosted model with a stricter prompt would be the correct choice.

---

## Known Limitations and Future Work

### Document Isolation
Session-based isolation uses `session_id` filtering. There is no authentication — any client that knows a `session_id` can access its documents. Adding JWT-based auth with user accounts would be the production path.

### XLSX/CSV Analytical Queries
Row-batched embedding works for semantic questions ("what does this table say about region X") but loses precision for aggregations ("total sales in Q1"). A text-to-SQL agent over a temporary SQLite table would handle these correctly — planned as a future extension.

### PDF Quality
pdfplumber struggles with two-column academic layouts and math symbols. For high-quality academic PDF ingestion, `pymupdf` with layout analysis provides better results.

### Embedding Dimension
The schema uses `VECTOR(1536)` for `text-embedding-3-small`. Switching embedding models requires a schema migration and full re-ingestion of all documents.

### Session Persistence
In-memory session store is lost on server restart. Redis would provide durable session storage for multi-instance deployments.

### Concurrency
File extraction is wrapped in `asyncio.to_thread` to avoid blocking the event loop. Under high concurrent ingestion load, the default `ThreadPoolExecutor` (CPU count × 5 threads) may become a bottleneck — a dedicated thread pool with tuned size would be appropriate.