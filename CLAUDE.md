# SmartFeed

Personal RSS aggregator with topic classification, semantic search, and AI-powered summaries, focused on technology content. Designed for non-technical users with a modern, polished UI.

## Project Overview

SmartFeed is a self-hosted RSS reader that goes beyond basic feed reading:
- Fetches and stores articles from RSS/Atom feeds
- Classifies articles into topics automatically (zero-shot via embeddings)
- Enables semantic search across all stored articles
- Generates AI summaries using a configurable LLM (local or cloud)
- Beautiful, easy-to-use web interface built with Next.js + shadcn/ui

## Architecture

Monorepo with two clearly separated services. If the project outgrows this setup, each service can be split into its own repo with no refactoring — just `git subtree split`.

```
smartfeed/
├── backend/                    # Python — FastAPI
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/
│   │   └── app/
│   │       ├── core/           # Domain models, interfaces, config
│   │       ├── ingestion/      # RSS fetching
│   │       ├── processing/     # Classification, embeddings, summarization
│   │       ├── storage/        # PostgreSQL + pgvector (articles + embeddings)
│   │       ├── services/       # FeedSyncService — orchestrates sync pipeline
│   │       ├── jobs/           # ARQ job queue + worker (ArqJobQueue, WorkerSettings)
│   │       ├── api/            # FastAPI REST endpoints
│   │       └── cli/            # Typer CLI for ops
│   └── tests/
│
├── frontend/                   # TypeScript — Next.js
│   ├── messages/               # i18n translation files (en, es, de)
│   ├── package.json
│   └── src/
│       ├── app/
│       │   ├── page.tsx            # Root redirect → /en/articles
│       │   └── [locale]/           # Locale-prefixed routes (en/es/de)
│       │       ├── layout.tsx      # HTML lang attr + NextIntlClientProvider
│       │       ├── articles/
│       │       ├── feeds/
│       │       └── search/
│       ├── components/         # shadcn/ui + custom components
│       ├── contexts/           # SyncContext — global sync job state
│       ├── hooks/              # Custom React hooks (useArticles, useSearch, …)
│       ├── i18n/               # next-intl config (routing.ts, request.ts)
│       ├── lib/                # API client, constants, utilities
│       ├── middleware.ts       # Locale detection + redirect
│       ├── navigation.ts       # Locale-aware Link / useRouter / usePathname
│       └── types/              # TypeScript types (mirrored from backend schemas)
│
└── docker-compose.yml          # Runs postgres, redis, backend, worker, frontend
```

### Backend layer rules

The `src/app/` layout follows the PyPA standard — prevents accidental imports from the project
root during testing.

The `core/` layer defines abstract interfaces (`FeedRepository`, `VectorStore`, `Summarizer`).
All other layers depend inward — storage and processing implement those interfaces.
API and CLI depend only on `core/` abstractions.

## LLM Provider Strategy

Primary provider is **Ollama** (local, free, private). The system is provider-agnostic via
**`litellm`**, which gives a unified interface to all supported backends.

Switching providers requires only a `.env` change — no code changes.

### Supported providers

| Provider | Type | Model example |
|---|---|---|
| Ollama | Local | `ollama/llama3.2`, `ollama/mistral` |
| Anthropic (Claude) | Cloud | `claude-haiku-4-5`, `claude-sonnet-4-6` |
| OpenAI | Cloud | `gpt-4o-mini`, `gpt-4o` |
| OpenRouter | Cloud (aggregator) | `openrouter/mistralai/mistral-7b-instruct` |

### LLM configuration

```env
# Primary: local Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# To switch to Claude:
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-haiku-4-5
# ANTHROPIC_API_KEY=...

# To switch to OpenAI:
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
# OPENAI_API_KEY=...

# To switch to OpenRouter:
# LLM_PROVIDER=openrouter
# LLM_MODEL=openrouter/mistralai/mistral-7b-instruct
# OPENROUTER_API_KEY=...
```

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Package manager | `uv` |
| HTTP client | `httpx` (async) |
| RSS parsing | `feedparser` |
| Models / validation | `pydantic` v2 |
| Config | `pydantic-settings` + `.env` |
| ORM + DB | `SQLAlchemy` + PostgreSQL (`psycopg2`) |
| Vector store | `pgvector` (PostgreSQL extension, `Vector(768)` column) |
| Embeddings | Ollama `nomic-embed-text` via HTTP (768-dim) |
| LLM (primary) | Ollama — `llama3.2` or any local model |
| LLM (cloud fallback) | Claude, OpenAI, OpenRouter via `litellm` |
| REST API | `FastAPI` + `uvicorn` |
| Job queue | `arq` + Redis — non-blocking sync, cron auto-sync |
| CLI | `Typer` |
| Testing | `pytest` + `pytest-asyncio` |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript |
| UI components | `shadcn/ui` |
| Styling | Tailwind CSS v4 |
| i18n | `next-intl` — en / es / de, locale-prefixed routes |
| Package manager | `pnpm` |
| Data fetching | `TanStack Query` (React Query) |
| HTTP client | `ky` or native `fetch` |
| Testing | `Vitest` + `Testing Library` |

## Key Design Decisions

- **Monorepo, two services**: backend and frontend are cleanly separated from day one. No shared
  runtime, no shared package manager. Splitting into two repos later = `git subtree split`.
- **Next.js + shadcn/ui**: best-in-class visual quality out of the box, designed for non-technical
  users. shadcn/ui components are copy-owned — no version lock-in.
- **Ollama first**: local LLM, no API cost, no data leaving the machine. Cloud providers are
  available as opt-in via a single env var change.
- **`litellm` as LLM adapter**: one interface, 100+ providers. No N provider-specific clients.
- **PostgreSQL + pgvector**: single database for both relational data and vector embeddings — no separate vector store process, better performance, ACID guarantees. Runs via Docker (`pgvector/pgvector:pg17` image).
- **Topics as DB entities**: `topics` table holds `name` + `description`; seeded
  automatically on startup via `_migrate()`. `articles.topic_id` is a FK —
  no string duplication, referential integrity, rename = one row.
  `GET /api/topics` exposes them. Adding a topic requires only a DB row +
  backend restart (no code change).
- **Embeddings for classification**: topic descriptions come from the `topics`
  table at runtime, injected into `classify(text, topics)` by
  `FeedSyncService.enrich()` — classifier is decoupled from config and
  storage. Classified by cosine similarity, no training data needed, works
  fully offline.
- **Interfaces in `core/`**: swapping any backend (vector store, LLM, DB) requires only a new
  adapter — no business logic changes.
- **`next-intl` for i18n**: SEO-friendly locale-prefixed routes (`/en/`, `/es/`, `/de/`),
  server-side message loading, automatic browser locale detection via middleware.
  Switching language requires zero backend changes — purely frontend.
- **SOLID hooks pattern**: all data-fetching and mutation logic lives in custom hooks
  (`useArticles`, `useSearch`, `useFeedActions`, `useAddFeed`). Page components are
  pure presentation — no direct API calls in render. Each component calls its own
  `useTranslations`, no prop drilling.
- **Non-blocking sync with ARQ + Redis**: `POST /feeds/{id}/sync` enqueues an ARQ job
  and returns `202` in <10 ms. Worker runs `FeedSyncService` in a separate process
  and publishes to Redis Pub/Sub on completion.
- **Two-phase sync pipeline**: `sync_feed_job` (fast path, < 5 s) fetches and
  stores raw articles, fires the SSE `complete` event, then enqueues
  `enrich_articles_job`. The enrich job (slow path, background) runs
  classify + summarize + embed via Ollama and fires an `enriched` SSE event
  so the frontend refetches. Enrichment failures are silent — articles
  remain visible without topic/summary.
- **SSE for real-time notifications**: `GET /feeds/sync-events` streams Redis Pub/Sub
  events to the browser via Server-Sent Events. `SyncMonitor` holds one `EventSource`
  per tab — zero polling. On page refresh, recovers in-progress jobs from
  `localStorage` and does a one-time HTTP status check.
- **`asyncio.shield` in `_publish`**: the `finally` block in ARQ job functions uses
  `asyncio.shield` to protect the Redis publish from being cancelled when ARQ's
  `job_timeout` kills the task — ensures the SSE event always reaches the browser.
- **Centralized config**: all tunables (`embedding_model`, `embedding_dim`, char
  limits, concurrency, pagination, timeouts) live in `Settings` (pydantic-settings)
  and are overridable via `.env`. Frontend equivalents live in `lib/constants.ts`
  with `NEXT_PUBLIC_*` env var support.

## Development Commands

### Backend commands

```bash
cd backend
uv sync
uv run uvicorn app.api.main:app --reload   # http://localhost:8000
uv run arq app.jobs.worker.WorkerSettings  # ARQ worker (separate terminal)
uv run pytest
uv run ruff check . && uv run ruff format .
```

### Frontend commands

```bash
cd frontend
pnpm install
pnpm dev     # http://localhost:3000
pnpm build
pnpm test
```

### Full stack with Docker

```bash
docker compose up --build
# First time or after DB schema changes:
docker compose down -v && docker compose up --build
```

## Environment Variables

### Backend `backend/.env`

```env
DATABASE_URL=postgresql://smartfeed:smartfeed@localhost:5432/smartfeed
REDIS_URL=redis://localhost:6379
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
# All other tunables have defaults — see backend/.env.example
```

### Frontend `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Feed Topics (default)

Topics are stored in the `topics` table and seeded on first startup from `_SEED_TOPICS`
in `backend/src/app/storage/database.py`. Each topic has a `name` and a rich keyword
`description` used for zero-shot embedding classification.

Default topics: AI & ML, Web Development, DevOps, Programming Languages, Cybersecurity,
Open Source & Linux, Hardware & Electronics, Science & Research.

To add a topic: insert a row in `topics` and restart the backend (clears the embedding
cache — no code or config change needed).
