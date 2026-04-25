# SharePoint RAG Chatbot — Production-like Demo

A **zero-cost, fully local** RAG chatbot that demonstrates how to build a SharePoint knowledge assistant using:

- 🦙 **Ollama** — local LLM inference (Llama 3.1 by default)
- 🦙 **LlamaIndex** — RAG orchestration
- 🗄️ **FAISS** — local vector store (persisted across restarts)
- 🤗 **sentence-transformers/all-MiniLM-L6-v2** — local embeddings (no API key needed)
- 🎈 **Streamlit** — interactive chat UI with SharePoint metadata display
- 🐳 **Docker Compose** — two services (`ollama` + `app`), one command to run

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version ≥ 24)
- [Docker Compose](https://docs.docker.com/compose/install/) (version ≥ 2.20 — usually bundled with Docker Desktop)
- ~5 GB of free disk space (for the Ollama model)

### 1. Clone and configure

```bash
git clone https://github.com/kadija-kru/shareointchatbot.git
cd shareointchatbot

cp .env.example .env
# Edit .env if you want to change the model or other settings
```

### 2. Start the stack

```bash
docker compose up --build
```

On first run this will:
1. Build the Python app image
2. Start the Ollama service
3. Automatically pull the `llama3.1` model into Ollama (~4.7 GB)
4. Build the FAISS vector index from the mock documents
5. Start the Streamlit UI on **http://localhost:8501**

> **First-run note:** Pulling the model takes a few minutes depending on your internet speed. Watch the `app` container logs — it will say `Model 'llama3.1' is ready` before Streamlit starts.

### 3. Open the chatbot

Navigate to **http://localhost:8501**

Try asking:
- *"What is the annual leave entitlement?"*
- *"How do I report an IT security incident?"*
- *"What was the Q1 2024 EBITDA margin?"*
- *"How does the pension scheme work?"*

---

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATA_CONNECTOR` | `mock` | Connector to use (`mock` or `sharepoint`) |
| `DATA_DIR` | `/app/data/mock_docs` | Path to mock documents inside container |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Model to use (e.g. `mistral`, `llama3.2`) |
| `TOP_K` | `4` | Number of document chunks to retrieve per query |
| `STRICT_GROUNDED` | `true` | LLM answers from context only (`false` = allow general knowledge) |
| `INDEX_DIR` | `/app/.index` | Container path for FAISS index persistence |
| `APP_PORT` | `8501` | Host port for the Streamlit UI |

---

## Project Structure

```
shareointchatbot/
├── app/
│   ├── app.py                         # Streamlit UI
│   ├── connectors/
│   │   └── mock_connector.py          # Mock SharePoint connector with metadata
│   └── rag/
│       ├── indexer.py                 # FAISS index build / load
│       └── retriever.py              # RAG query engine (Ollama + LlamaIndex)
├── data/
│   └── mock_docs/                     # Realistic Contoso mock documents
│       ├── hr_policy.md
│       ├── it_security_policy.md
│       ├── onboarding_guide.md
│       ├── project_management_templates.md
│       ├── q1_2024_business_report.md
│       └── benefits_compensation_guide.md
├── docs/
│   └── sharepoint-connector-design.md # Future real SharePoint connector design
├── .env.example                       # Environment variable template
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh                      # Waits for Ollama, pulls model, starts app
└── requirements.txt
```

---

## Features

### Streamlit UI
- 💬 Multi-turn chat interface
- 📚 **Sources expander** per answer — shows for each source:
  - Document title (linked to mock SharePoint URL)
  - Library name
  - Owner
  - Last modified date
  - Relevant snippet
- 📋 **Sidebar document list** — browse all indexed documents with metadata
- �� **Rebuild Index** button — force re-index without restarting the container
- ⚙️ Settings panel showing current configuration

### RAG Pipeline
- Local embeddings (no API key, no cost)
- FAISS vector index persisted to a Docker volume (`index_data`)
- Strict grounded mode: LLM is instructed to answer only from retrieved context
- Configurable Top-K retrieval

---

## Rebuild the Index

If you add documents to `data/mock_docs/` and want to re-index:

```bash
# Option 1: use the UI button (Sidebar → Rebuild Index)

# Option 2: restart the app service
docker compose restart app

# Option 3: delete the index volume and restart
docker compose down -v && docker compose up
```

---

## Changing the LLM Model

Edit `.env`:

```bash
OLLAMA_MODEL=mistral   # or llama3.2, phi3, gemma2, etc.
```

Then restart:

```bash
docker compose restart app
```

The entrypoint script will automatically pull the new model on startup.

---

## Connecting to Real SharePoint (Future)

See [`docs/sharepoint-connector-design.md`](docs/sharepoint-connector-design.md) for the full design covering:

- Entra ID delegated auth (on-behalf-of user)
- Required Graph API permissions
- Core Graph endpoints for site discovery, file listing, and search
- Permission-safe approach (delegated tokens only, never app-only)
- Incremental indexing with Graph delta queries
- Security and content isolation notes

---

## Stopping

```bash
docker compose down          # stop containers, keep volumes (index is preserved)
docker compose down -v       # stop and delete all volumes (index will rebuild on next start)
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Ollama never becomes healthy | Check `docker compose logs ollama`. Ensure port 11434 is not in use. |
| Model pull fails / times out | Check your internet connection. Try `OLLAMA_MODEL=phi3` (smaller). |
| Index build fails | Check `docker compose logs app`. Ensure `DATA_DIR` contains `.md` files. |
| Streamlit shows "Failed to initialise" | Ollama may still be loading. Wait 30s and refresh. |
| Out of memory during model load | Use a smaller model: `OLLAMA_MODEL=phi3` or `OLLAMA_MODEL=tinyllama`. |

---

## Architecture

```
Browser
  │
  ▼
Streamlit (port 8501)
  │  ┌─────────────────────────────────────┐
  │  │  LlamaIndex RAG Pipeline           │
  │  │  ┌──────────┐  ┌────────────────┐  │
  │  │  │  FAISS   │  │  Ollama LLM    │  │
  │  │  │  Index   │  │  (llama3.1)    │  │
  │  │  │ (volume) │  │  port 11434    │  │
  │  │  └──────────┘  └────────────────┘  │
  │  └─────────────────────────────────────┘
  │
  ▼
Answer + SharePoint metadata (title, library, owner, date, URL)
```

---

*Costs: £0 / $0 — all computation is local.*
