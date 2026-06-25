A RAG-based document Q&A system that extracts, indexes, and answers questions from multi-format documents with full source traceability.

## Features

- Multi-format ingestion: PDF, DOCX, PPTX, XLSX, CSV, TXT
- Structure-aware chunking for PDF and DOCX (heading-based segmentation)
- Source citations on every answer (file name, page/slide/sheet/row)
- Session-scoped document isolation — each session has its own knowledge base
- LangSmith monitoring (optional)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| Vector DB | PostgreSQL + pgvector |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |
| Frontend | React + Vite + Nginx |
| Container | Docker + Docker Compose |
| Reverse Proxy | Caddy (auto SSL) |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/brilbrilbril/chat-with-pdf.git
cd chat-with-pdf
```

### 2. Set up environment

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

```bash
# Required
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=http://host.docker.internal:8080/v1
OPENAI_EMBEDDING_URL=http://host.docker.internal:8081/v1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cwp_db
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/cwp_db
EMBEDDING_MODEL=Qwen-embedding
LLM_MODEL=Qwen3.5-4B


CHUNK_SIZE=1500
CHUNK_OVERLAP=200

TOP_K=10
MAX_TOKENS=80000

# Optional — LangSmith monitoring
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=doc-intelligence
LANGCHAIN_TRACING_V2=true
```

### 3. Start PostgreSQL

```bash
docker compose up -d postgres
```

Wait for it to be healthy:

```bash
docker compose ps
```

### 4. Install backend dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Initialize the database

```bash
python scripts/initdb.py
```

### 6. Run the backend

```bash
uvicorn src.api.main:app --reload --port 3000
```

API is available at `http://localhost:3000`
Swagger UI at `http://localhost:3000/docs`

### 7. Run the frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:5173`

---

## Running with Docker Compose (RECOMMENDED)

```bash
# Build and start all services
docker compose -f docker-compose.yaml up -d --build

# Initialize DB (first time only)
docker exec cwp_backend python scripts/initdb.py

# View logs
docker compose logs -f backend
```

Services:

| Service | Port |
|---------|------|
| Backend API | 3000 or 8000 (via docker) |
| Frontend | 5173 or 80 (via docker) |
| PostgreSQL | 5433 (host) |

---

## API Endpoints

### Documents

```
POST   /documents/upload              Upload and ingest a document
GET    /documents?session_id=...      List documents for a session
DELETE /documents              Delete all document and its chunks
```

### Chat

```
POST   /chat                          Send a message (returns full response)
POST   /chat/stream                   Send a message (SSE streaming)
GET    /chat/sessions/{id}/history    Get session message history
DELETE /chat/sessions/{id}            Clear session history and documents
```

### Upload example

```bash
curl -X POST http://localhost:3000/documents/upload \
  -F "file=@yourfile.pdf" \
  -F "session_id=my-session-123"
```

### Chat example

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my-session-123", "message": "What is the audit procedure?"}'
```

### SAMPLE Q&A
PDF:
siapa yang dikenakan wajib pajak badan?
jelaskan mengenai wajib pajak orang pribadi
siapa yang tidak termasuk wajib pajak?

word:
jelaskan mengenai penyakit ginjal kronis
ringkas pembukaan UUD1945

excel:
how about troubleshooting AWS IAM?
tell me the abstract about understanding cicd
explain me about clinical evaluation of migraine

txt:
bagaimana kebijakan reschedule? -> follow up keyword or query = "kebijakan reschedule"
bagaimana kebijakan pengiriman logistik?


PPT:
Kriteria Steganografi Yang Bagus
jelaskan mengenai perubahan warna pada steganografi


### SAMPLE DOCS
You can use documents from sample_docs directory. **remember: make sure you delete all documents before uploading new document**

### IMPORTANT NOTE
1. The current deployed app is one-session only, so to overcome the problem of documents being hit because there is still no suitable filter, please **delete the uploaded file before uploading a new file.**

2. Because this project for demo uses **PAID API AND VPS**, so expect the termination server on **28th June 2026**

3. If somehow the LLM or embedding is error, it might be the **credit runs out.**

4. I will periodically **delete** the documents every 3 hours.
---

## Production Deployment

See [TECHNICAL.md](TECHNICAL.md) for architecture details.

### Prerequisites on VPS

- Docker + Docker Compose
- Caddy (for SSL and reverse proxy)
- Domain with A record pointing to VPS IP

### One-time VPS setup

```bash
# Create app directory
mkdir -p /opt/chat-with-pdf
cd /opt/chat-with-pdf

# Copy compose files and environment
scp docker-compose.yaml docker-compose.prod.yaml .env user@vps:/opt/chat-with-pdf/

# Pull and start
DOCKER_USERNAME=yourdockerhubusername \
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d

# Initialize DB
docker exec cwp_backend python scripts/init_db.py
```

### Caddy configuration

```bash
sudo nano /etc/caddy/Caddyfile
```

```
yourdomain.com {
    reverse_proxy localhost:3000
}
```

```bash
sudo systemctl enable caddy
sudo systemctl restart caddy
```

### CI/CD

Push to `main` → GitHub Actions builds and pushes Docker images → SSH into VPS → pull images → restart containers.

Required GitHub Secrets:

```
DOCKER_USERNAME    Docker Hub username
DOCKER_PASSWORD    Docker Hub access token
VPS_HOST           VPS IP or domain
VPS_USER           SSH user
VPS_SSH_KEY        Private SSH key
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `POSTGRES_USER` | Yes | PostgreSQL user |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `POSTGRES_DB` | Yes | PostgreSQL database name |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `EMBEDDING_MODEL` | Yes | Embedding model name |
| `LLM_MODEL` | Yes | LLM model name |
| `EMBEDDING_BASE_URL` | Yes | OpenAI Compatible |
| `LLM_BASE_URL` | Yes | OpenAI Compatible |
| `CHUNK_SIZE` | Yes | Chunk size in words (default: 1500) |
| `CHUNK_OVERLAP` | Yes | Overlap in words (default: 200) |
| `TOP_K` | Yes | Number of chunks to retrieve (default: 10) |
| `MAX_TOKENS` | Yes | Max context tokens (default: 80000) |
| `LANGCHAIN_API_KEY` | ❌ | LangSmith API key (enables monitoring) |
| `LANGCHAIN_PROJECT` | ❌ | LangSmith project name |
| `LANGCHAIN_TRACING_V2` | ❌ | Enable LangSmith tracing |