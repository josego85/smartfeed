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
│       ├── proxy.ts            # Locale detection + redirect (Next.js 16 convention)
│       ├── navigation.ts       # Locale-aware Link / useRouter / usePathname
│       └── types/              # TypeScript types (mirrored from backend schemas)
│
└── docker-compose.yml          # Runs postgres, redis, backend, worker, frontend
```

### Backend layer rules

The `src/app/` layout follows the PyPA standard — prevents accidental imports from the project
root during testing.

The `core/` layer defines abstract interfaces (`FeedRepository`, `VectorStore`, `Summarizer`, `Classifier`).
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
| Testing | `pytest` + `pytest-asyncio` + `respx` + `pytest-cov` |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript |
| UI components | `shadcn/ui` |
| Styling | Tailwind CSS v4 |
| i18n | `next-intl` — en / es / de, locale-prefixed routes |
| Package manager | `pnpm` |
| Data fetching | `TanStack Query` (React Query) |
| HTTP client | `ky` or native `fetch` |
| Testing | `Vitest` + `Testing Library` |

## Testing Strategy

Three-tier pyramid. `e2e` marker is excluded from the default `addopts` — CI runs
unit + integration without Docker; e2e are opt-in.

```text
tests/
├── conftest.py                      # shared fixtures (Feed, Article, Topic)
├── unit/                            # no I/O — all external calls mocked
│   ├── core/test_models.py          # Pydantic domain model contracts
│   ├── core/test_config.py          # Settings / env overrides
│   ├── ingestion/test_fetcher.py    # RSS/Atom parser (httpx via respx)
│   ├── processing/test_classifier.py
│   ├── processing/test_summarizer.py
│   ├── processing/test_embeddings.py
│   └── services/test_sync_service.py
├── integration/api/                 # FastAPI TestClient + dependency_overrides
│   ├── test_feeds.py
│   ├── test_articles.py
│   ├── test_search.py
│   ├── test_topics.py
│   └── test_health.py
└── e2e/storage/                     # real PostgreSQL — docker-compose.test.yml
    └── test_repository.py           # typed against FeedRepository (interface, not impl)
```

### Key testing decisions

- **`test_repository.py` typed as `FeedRepository`** (DIP): contract tests verify
  the interface, not the concrete class. Swapping `PostgresRepository` for another
  adapter requires zero test changes.
- **`e2e/conftest.py` patches both `database.engine` and `postgres_repo.engine`**:
  `postgres_repo.py` imports `engine` by value at module load time; patching only
  `database.engine` would leave the repo using the prod engine.
- **`_clean_tables` truncates `feeds CASCADE`** between e2e tests — cascades to
  articles, leaves seeded `topics` intact.
- **`docker-compose.test.yml`** runs postgres on port **5433** (offset from dev 5432)
  so both stacks can run simultaneously.
- **`TEST_DATABASE_URL` env var** overrides the default test DB URL for CI pipelines.

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
- **Embedding-based classification via `Classifier` interface**: `Classifier` ABC in
  `core/interfaces.py` (same pattern as `Summarizer`). `EmbeddingClassifier` in
  `processing/classifier.py` embeds the article (Ollama `nomic-embed-text`, same
  pipeline as semantic search) and picks the topic whose description embedding has
  the highest cosine similarity — no LLM completion call, so it's deterministic and
  cheap. Topic embeddings are computed once per process and cached in-memory
  (topic id + description as key); topics list is always fetched from DB at runtime
  and injected by `FeedSyncService.enrich()` — no code change needed to add/rename
  a topic, only a process restart to pick up the new embedding.
  If the best match is below `classify_confidence_threshold` (default 0.55), the
  article is assigned the seeded **"Other"** topic instead of being force-fit into
  an engineering-specific one — this is what an off-topic consumer-tech article
  (e.g. a smartphone feature roundup) should land in instead of "Programming".
  Topic seed data lives in `storage/seeds.py` (separate from schema).
  Articles are ordered by `published_at DESC NULLS LAST`.
- **Interfaces in `core/`**: swapping any backend (vector store, LLM, DB) requires only a new
  adapter — no business logic changes.
- **`next-intl` for i18n**: SEO-friendly locale-prefixed routes (`/en/`, `/es/`, `/de/`),
  server-side message loading, automatic browser locale detection via `proxy.ts`.
  Switching language requires zero backend changes — purely frontend.
- **`proxy.ts` (Next.js 16)**: Next.js 16 renamed the `middleware` file convention to `proxy`.
  File is at `src/proxy.ts`; content uses `createMiddleware` from `next-intl/middleware` unchanged.
- **`force-dynamic` on `[locale]/layout.tsx`**: all pages under the locale layout fetch live
  API data — static prerendering has no value and breaks when `NODE_ENV` is not `production`.
  A single `export const dynamic = "force-dynamic"` on the layout covers all child routes.
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
- **Feed title/description auto-populated on first sync**: `fetch_feed` returns a
  `FetchResult` dataclass (`title`, `description`, `articles`) instead of a bare
  `list[Article]`. `FeedSyncService.sync()` calls `FeedRepository.update_feed_metadata()`
  after the first successful fetch — idempotent: only writes when the field is empty,
  preserving future manual edits.
- **`ca-certificates` in backend Dockerfile**: `python:3.12-slim` ships without system
  CA certificates; `httpx`/`anyio` TLS handshake fails silently with `ConnectError`
  for all HTTPS feeds. `backend/Dockerfile` installs `ca-certificates` via
  `apt-get install --no-install-recommends ca-certificates`.

## Development Commands

### Backend commands

```bash
cd backend
uv sync
uv run uvicorn app.api.main:app --reload   # http://localhost:8000
uv run arq app.jobs.worker.WorkerSettings  # ARQ worker (separate terminal)
uv run pytest                              # unit + integration (no Docker needed)
uv run pytest --cov=app --cov-report=html  # with coverage report
uv run ruff check . && uv run ruff format .
```

### Backend e2e tests (require Docker)

```bash
cd backend
docker compose -f docker-compose.test.yml up -d   # starts postgres on port 5433
uv run pytest -m e2e -v                           # contract tests against real DB
docker compose -f docker-compose.test.yml down -v
```

### Frontend commands

```bash
cd frontend
pnpm install
pnpm dev     # http://localhost:3000
pnpm build   # forces NODE_ENV=production (dev container sets development — would break build)
pnpm test
```

### Git hooks (Husky)

Hooks live in `.husky/` at repo root. Activated once per clone by running `pnpm install`
inside `frontend/` (the `prepare` script runs husky from the repo root — no root-level
`package.json`).

- **pre-commit**: ruff check + format (backend) and biome ci (frontend) — only if relevant
  files are staged; skips cleanly if neither backend Python nor frontend TS/JS files changed
- **pre-push**: `pytest --ignore=tests/e2e` + `pnpm type-check`

CI (GitHub Actions) remains the authoritative gate — hooks are a fast local feedback layer.

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

## CI/CD (GitHub Actions)

Four workflow files under `.github/workflows/` + Dependabot config.

### `ci-backend.yml`

Triggers on push/PR to `main` when `backend/**` changes. Three jobs:

- **lint** — `ruff check` + `ruff format --check`
- **test-unit-integration** — `pytest --ignore=tests/e2e`; uploads `coverage.xml` artifact
- **test-e2e** — only on push to `main` (not PRs); uses a GH Actions service container (`pgvector/pgvector:pg17` on port 5433); needs lint + unit/integration to pass first

### `ci-frontend.yml`

Triggers on push/PR to `main` when `frontend/**` changes. Four jobs (fan-in):

- **lint** — `biome ci .` (read-only — do NOT use `pnpm lint` which has `--write`)
- **type-check** — `pnpm type-check`
- **test** — `vitest run --passWithNoTests`
- **build** — `pnpm build`; caches `.next/cache` keyed on `pnpm-lock.yaml`; needs all three above

### `security.yml`

Triggers on push/PR to `main` and weekly (Monday 03:00 UTC). Jobs:

- **codeql** — matrix `[python, javascript-typescript]`; `security-and-quality` queries; uploads SARIF
- **audit-backend** — `uv export --no-dev` → `uvx pip-audit --require-hashes`
- **audit-frontend** — `pnpm audit --audit-level=high`

### `dependabot.yml`

Weekly on Monday 04:00 `America/Asuncion` for `pip`, `npm`, and `github-actions`. Dev minor/patch bumps are grouped into a single PR per ecosystem. Action SHAs are auto-bumped.

### Security practices for workflows

- All actions pinned to full commit SHA (e.g. `actions/checkout@de0fac2e...`)
- `permissions: contents: read` at workflow level; CodeQL adds `security-events: write` only where needed
- `concurrency.cancel-in-progress: true` on PRs to avoid queue buildup

## Feed Topics (default)

Topics are stored in the `topics` table and seeded on first startup from `_SEED_TOPICS`
in `backend/src/app/storage/database.py`. Each topic has a `name` and a rich keyword
`description` used for zero-shot embedding classification.

Default topics: AI & ML, Web Development, DevOps, Programming Languages, Cybersecurity,
Open Source & Linux, Hardware & Electronics, Science & Research, Consumer Tech & Gadgets
(smartphones, routers, wearables, TVs, and other consumer device reviews/buying guides —
distinct from the engineering-focused Hardware & Electronics), Other (catch-all for
consumer/general tech content that doesn't fit any topic above).

To add a topic: insert a row in `topics` and restart the backend (clears the embedding
cache — no code or config change needed).
