# Sofia Real Estate Analysis

An AI-powered real estate assistant for the Sofia, Bulgaria housing market. Data is gathered by scraping a Bulgarian real estate website and stored in SQLite + a Qdrant vector database.

---

## Agent capabilities

The chat interface routes user queries to the appropriate tool automatically:

| User intent | Tool | Data source |
|---|---|---|
| Find listings ("show me 2-bed apartments in Лозенец") | `search_listings` | Hard constraint filter → Qdrant vector search → SQLite metadata join |
| Market statistics ("avg price in Младост?") | `get_stats` | SQLite aggregation on `ads_cleaned` |
| Neighbourhood comparison ("compare avg price/sqm between Лозенец and Витоша") | `get_stats` × 2 (parallel) | SQLite |

All prices are returned in EUR. Neighbourhood names are stored in Bulgarian Cyrillic — the LLM translates user input automatically before querying.

---

## Stack

**Backend**
- FastAPI — single app with `/search` and `/chat` endpoints (`api/app.py`)
- OpenAI `gpt-4o` — tool-calling agent loop (`agent/main.py`)
- SQLite — cleaned listings (`ads_cleaned` table)
- Qdrant — vector embeddings for semantic search
- `python-dotenv` — loads `backend/.env` for API keys

**Frontend**
- React + Vite + TypeScript
- Calls `/chat` for all user messages; renders listing cards when search results are returned, plain text for analytics answers

---

## Running locally

**Backend**
```bash
cd backend
uvicorn api.app:app --reload
```

**Frontend**
```bash
cd frontend
bun run dev
```

**Environment variables** — create `backend/.env`:
```
OPENAI_API_KEY=sk-...
QDRANT_API_KEY=...
QDRANT_CLUSTER_URL=https://...
```
