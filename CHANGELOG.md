# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) —
[Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

### Backend

#### Added

- `enrich_articles_job`: new ARQ background job — classify, summarize,
  and embed articles after sync; publishes `enriched` SSE event so the
  frontend refetches automatically without frontend changes
- `FeedSyncService.enrich()`: isolated slow path for LLM enrichment,
  called exclusively by `enrich_articles_job`
- `FeedRepository.get_articles_by_ids()` and
  `update_article_enrichment()`: new interface methods +
  `PostgresRepository` implementations
- FastAPI REST API: feeds CRUD, article listing with topic/feed
  filters, semantic search
- PostgreSQL + pgvector: relational data and `Vector(768)` embeddings
  in one DB
- `PostgresRepository` and `PgVectorStore` implementing `core/`
  interfaces — swappable without touching business logic
- Zero-shot topic classifier via Ollama embeddings
  (`nomic-embed-text`) — keyword descriptions, no training data needed
- RSS/Atom ingestion with browser `User-Agent` to avoid 403s
- LLM summarization via `litellm` — Ollama by default,
  Claude/OpenAI/OpenRouter via single env var swap
- Typer CLI: `feeds_add`, `feeds_list`, `feeds_sync`, `search`
- Dependency pinning with exact versions (reproducibility, fast builds)
- `FeedSyncService`: deduplication with one bulk DB query, bulk insert
  via `ON CONFLICT DO NOTHING`
- ARQ + Redis background job queue: `POST /feeds/{id}/sync` returns
  `202 Accepted` in <10 ms; sync runs in a separate worker process
- ARQ cron job (`sync_all_feeds_job`): auto-sync every 30 min through
  the same `FeedSyncService` path
- `GET /feeds/sync-events` SSE endpoint backed by Redis Pub/Sub:
  worker publishes on completion, browser notified in ~50 ms — no
  polling
- `GET /feeds/{id}/sync-status` for one-time check on page refresh
- All tunables in `Settings` (pydantic-settings), overridable via
  `.env`: HTTP timeout, embedding model/dim, char limits,
  concurrency, pagination, worker settings

#### Changed

- `FeedSyncService.sync()` is now a fast path (fetch + store raw,
  < 5 s); LLM enrichment delegated to `enrich_articles_job` — sync
  completes and notifies the browser before any Ollama call is made
- `cli feeds_sync` uses `FeedSyncService` — was one-by-one inline sync
- Embedding dimension corrected 384 → 768 (`nomic-embed-text` actual)
- `embedding_model` and `embedding_dim` moved to `Settings`

#### Removed

- APScheduler (`apscheduler` dependency) — replaced by ARQ cron job
- `FeedRepository.save_article()` — replaced by `save_articles_bulk`

#### Fixed

- `sync_feed_job` bare `await` in `finally` block was cancelled by
  ARQ's `job_timeout`, silently dropping the SSE event and leaving the
  UI stuck on "syncing" forever; replaced with `asyncio.shield` via a
  `_publish` helper

---

### Frontend

#### Added

- Next.js 15 App Router with `shadcn/ui` and Tailwind CSS v4
- Feed management: add, list, sync, delete
- Article listing with topic filter and read/unread tracking
- Semantic search with ranked results and similarity score
- TanStack Query: cache, deduplication, invalidation on sync completion
- i18n via `next-intl`: EN/ES/DE, locale-prefixed routes
  (`/en/`, `/es/`, `/de/`)
- `LanguageSwitcher` segmented-control component
- Translation files (`messages/en.json`, `es.json`, `de.json`)
- `SyncContext` + `SyncProvider`: global sync job state persisted in
  `localStorage` — survives navigation and page refresh (SSR-safe)
- `SyncMonitor`: single `EventSource` to `/feeds/sync-events`;
  invalidates TanStack Query cache on completion; one-time HTTP check
  for jobs recovered from `localStorage` after refresh
- `SyncStatusSection` in Sidebar: live progress per job
- `SyncButton` in feeds page: real-time state per feed
- `lib/constants.ts`: all tunables in one place, each overridable via
  `NEXT_PUBLIC_*` build-time env var

#### Changed

- Routes under `src/app/[locale]/` — middleware auto-detects locale
- `useFeedActions` tracks enqueued job via `SyncContext`
- `BASE_URL` exported from `lib/api.ts` — no duplication
- `TERMINAL_STATUSES` moved from context to `lib/constants.ts`
- `QueryClient`: `staleTime: 30 s`, `refetchOnWindowFocus: false`
- SOLID hooks: pages are pure presentation, no direct API calls
- Each component calls its own `useTranslations` — no prop drilling

#### Fixed

- `ArticleCard` "Read" link hardcoded English — now uses active locale
- `formatDate` ignored locale — relative dates now render correctly

---

### Infrastructure

#### Added

- Docker Compose: `pgvector/pgvector:pg17`, named volume `pgdata`,
  backend startup gated on DB healthcheck
- Redis service (`redis:7-alpine`) with healthcheck
- ARQ worker service — same image as backend,
  `uv run arq app.jobs.worker.WorkerSettings`
