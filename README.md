# Agentic RAG Research Assistant

A production-ready multi-agent research assistant built with **LangGraph**, **LangChain**,
**Groq** (primary LLM), **ChromaDB**, **Sentence Transformers**, **Tavily Search**, **SQLite**,
and a **professionally themed multi-page Streamlit dashboard**.

## Features

- Multi-Agent Architecture (8 specialized agents)
- LangGraph orchestration with parallel retrieval branches
- **Live pipeline visualization** — watch each agent execute in real time
- PDF upload & ingestion into a persistent vector store (single + bulk upload)
- Agentic RAG with query rewriting
- Web research via Tavily
- Hallucination detection & confidence scoring
- Source citations (documents + web) with styled citation cards
- Persistent conversation memory (SQLite)
- Markdown research report generation
- **Multi-page dashboard**: Chat, Documents, Analytics, Reports, History
- Chat export (Markdown / JSON / TXT)
- Document management (view, bulk-upload, delete from vector store)
- Analytics dashboard with confidence/hallucination trend charts
- Session history management (rename, export, delete)
- Optional Claude-based secondary verification
- Custom dark theme with professional styling
- Centralized logging & error handling throughout
- **Render deployment ready** + **optional Docker**

## Architecture

```
User Query
   ↓
Supervisor Agent          (decides RAG / Web / both)
   ↓
Query Rewriter Agent       (standalone, context-aware query)
   ↓
   ├── Retriever Agent  ──┐   (parallel)
   └── Web Research Agent─┘
   ↓
Verification Agent         (checks context sufficiency)
   ↓
Hallucination Checker Agent (drafts answer + scores grounding)
   ↓
Report Generator Agent     (Markdown report + citations)
   ↓
Memory Agent               (persists conversation + report)
   ↓
Final Response (Streamlit, streamed live)
```

## Project Structure

```
agentic_rag_assistant/
├── app.py                   # Main Chat page (Streamlit entrypoint)
├── config.py                 # Pydantic settings
├── logger.py                  # Centralized logging
├── requirements.txt
├── .env.example
├── Procfile                    # Render process definition
├── render.yaml                  # Render blueprint
├── runtime.txt                   # Python version pin
├── Dockerfile                      # Optional container build
├── docker-compose.yml               # Optional local container orchestration
├── .dockerignore
├── .streamlit/
│   └── config.toml                   # Custom theme
├── agents/                             # All 8 agents
├── graph/                                # LangGraph state & workflow
├── rag/                                   # Vector store, ingestion, retriever
├── memory/                                 # Conversation memory
├── database/                                # SQLite models & connection
├── utils/                                     # PDF loader, splitter, LLM clients
├── ui/                                          # Styling, export, components
├── pages/                                        # Multi-page Streamlit app
│   ├── 1_Documents.py
│   ├── 2_Analytics.py
│   ├── 3_Reports.py
│   └── 4_History.py
├── reports/                                        # Generated research reports
└── tests/                                            # Unit tests
```

## Local Setup

### 1. Create a virtual environment (Python 3.12)

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

- `GROQ_API_KEY` — **required**. Get one at https://console.groq.com
- `TAVILY_API_KEY` — **required** for web search. Get one at https://tavily.com
- `ANTHROPIC_API_KEY` — **optional**, only used for secondary verification.

### 4. Run the application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`. Use the sidebar navigation to
switch between **Chat**, **Documents**, **Analytics**, **Reports**, and **History** pages.

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Deployment

### Option A — Render (recommended, no Docker needed)

1. Push this repository to GitHub.
2. In Render, click **New → Blueprint** and select your repo (it will auto-detect `render.yaml`).
   - Alternatively, create a **New → Web Service** manually:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:**
       ```
       streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false
       ```
3. In the Render dashboard, set the required environment variables (these are marked
   `sync: false` in `render.yaml` so Render will prompt you to enter them securely):
   - `GROQ_API_KEY`
   - `TAVILY_API_KEY`
   - `ANTHROPIC_API_KEY` (optional)
4. **Important — common Render pitfalls:**
   - Render injects a `$PORT` env var; the start command **must** bind to `0.0.0.0:$PORT`
     (already handled in `Procfile` / `render.yaml`).
   - `enableXsrfProtection` must be `false` behind Render's reverse proxy, or file
     uploads and chat input may silently fail.
   - The free Render plan sleeps after inactivity — the first request after sleep
     can take 30-60s while the container restarts and reloads the embedding model.
   - ChromaDB and SQLite write to local disk, which is **ephemeral** on Render's
     free tier (data resets on redeploy/restart). The `render.yaml` attaches a
     persistent disk to `chroma_db/` for paid plans; for free tier, treat the
     vector store as session-scoped.

### Option B — Docker (optional, for self-hosting / VPS)

```bash
cp .env.example .env   # fill in your API keys
docker compose up --build
```

The app will be available at `http://localhost:8501`. Data in `chroma_db/`,
`database/`, `reports/`, and `logs/` is persisted via bind mounts.

To build and run without compose:

```bash
docker build -t agentic-rag-assistant .
docker run -p 8501:8501 --env-file .env \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/reports:/app/reports \
  agentic-rag-assistant
```

---

## Usage

1. **Chat page**: Ask a research question. Watch the live pipeline tracker show each
   agent (Supervisor → Query Rewriter → Retriever/Web Research → Verifier →
   Hallucination Checker → Report Generator → Memory) execute in real time.
2. **Documents page**: Bulk-upload PDFs, view indexed document stats, or remove a
   document (and its vectors) from the knowledge base.
3. **Analytics page**: View aggregate stats — total sessions, queries, documents,
   average confidence/hallucination scores, and trend charts over time.
4. **Reports page**: Browse, search, filter (by confidence), preview, and download
   all generated Markdown research reports.
5. **History page**: Rename sessions, export full conversations (MD/JSON/TXT), or
   delete old sessions.

Expand **📊 Details & Sources** under any assistant response to view confidence
scores, hallucination flags, cited sources, and download the full report.

## Notes

- ChromaDB data persists in `./chroma_db/`.
- SQLite database lives at `./database/app.db`.
- Logs are written to `./logs/app.log` (rotating, 5MB x 3 backups).
- Generated reports are saved to `./reports/`.
- The custom dark theme is defined in `.streamlit/config.toml` and `ui/styles.py`.
