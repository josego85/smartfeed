# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) —
[Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Backend

#### Added

- `is_deleted` column (`BOOLEAN NOT NULL DEFAULT FALSE`) on `articles` table —
  soft delete preserves the URL in `get_existing_urls`, preventing re-import
  on next feed sync
- `FeedRepository.delete_article()` abstract method +
  `PostgresRepository` implementation (sets `is_deleted = True`)
- `DELETE /api/articles/{id}` endpoint — returns `204 No Content`;
  responds `404` if article does not exist or is already deleted
- Idempotent `_migrate()` step adds `is_deleted` column to existing DBs
  with `ALTER TABLE … ADD COLUMN IF NOT EXISTS`

#### Changed

- `list_articles()` and `get_article()` filter `is_deleted = FALSE` —
  deleted articles are invisible to all API consumers
- `get_existing_urls()` intentionally does **not** filter deleted articles —
  ensures deleted URLs are never re-fetched on sync

---

### Frontend

#### Added

- `articlesApi.delete(id)` — `DELETE /api/articles/{id}`, returns `void`
- `useDeleteArticle` hook — TanStack Query mutation; invalidates
  `["articles"]` cache on success
- `AlertDialog` component (`components/ui/alert-dialog.tsx`) built on
  `@radix-ui/react-dialog` — shadcn/ui pattern, copy-owned
- Delete action in `ArticleCard` footer — trash icon always visible,
  `AlertDialog` confirmation prevents accidental deletes
- `@radix-ui/react-dialog@1.1.15` dependency (exact pin for
  reproducibility)
- `frontend/.npmrc`: `confirm-module-purge=false` — prevents pnpm v11
  from aborting on no-TTY environments (Docker, CI)
- i18n keys `delete`, `deleteConfirmTitle`, `deleteConfirmDescription`,
  `deleteConfirmCancel`, `deleteConfirmAction` in EN / ES / DE

#### Fixed

- Production build crashes with `useContext` error when `NODE_ENV=development` is inherited
  from the dev container — `NODE_ENV=production` now forced in `package.json` build script
  and `Dockerfile` builder stage
- `middleware.ts` → `proxy.ts`: Next.js 16 deprecates the `middleware` file convention
- `[locale]` layout marked `export const dynamic = "force-dynamic"` — pages that fetch
  live API data must not be statically prerendered
- `LanguageSwitcher` `<button>` missing `type="button"` — could accidentally submit a parent form
- Biome lint: `useNamingConvention` disabled for `src/types/**` — snake_case mirrors the
  backend JSON contract

---

### Infrastructure

#### Added

- `frontend/.gitignore` and `frontend/.dockerignore` — exclude `.pnpm-store/` (320 MB),
  `node_modules/`, and `.next/` from git tracking and Docker build context

---

## [0.0.1] - 2026-05-10

---

### Backend

#### Added

- `Classifier` ABC in `core/interfaces.py` — mirrors `Summarizer`;
  enables DI and swappable implementations
- `LLMClassifier` in `processing/classifier.py` — calls the configured
  LLM via `litellm` with `temperature=0`; topics loaded from DB at
  runtime (fully dynamic, no cache)
- `storage/seeds.py` — topic seed data separated from `database.py`;
  `database.py` now owns only schema and migrations
- `topics` table (`id`, `name`, `description`) — topics are now first-class
  DB entities; keyword descriptions seeded automatically on startup via
  idempotent `_migrate()` in `init_db()`
- `GET /api/topics` endpoint — returns the full topic list with descriptions
- `FeedRepository.list_topics()` abstract method + `PostgresRepository`
  implementation with `_to_topic()` mapper
- `_migrate()` in `database.py` — seeds topics, adds `topic_id` FK to
  `articles`, migrates existing string values to FK, drops legacy `topic`
  column; safe to run on every startup (all steps idempotent)
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
- RSS/Atom ingestion with browser `User-Agent` to avoid 403s
- LLM summarization via `litellm` — Ollama by default,
  Claude/OpenAI/OpenRouter via single env var swap
- Typer CLI: `feeds_add`, `feeds_list`, `feeds_sync`, `search`
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
- Dependency pinning with exact versions (reproducibility, fast builds)

#### Changed

- `FeedSyncService` receives `Classifier` via constructor injection
  (same pattern as `Summarizer`); classifier no longer imported directly
- `max_classify_chars` raised 500 → 2000; previous value cut most
  article content before the classifier had enough signal
- Topic descriptions rewritten from keyword bags to natural-language
  prose
- `_migrate()` topics upsert changed to `ON CONFLICT DO UPDATE SET
  description`; description changes apply on restart
- Articles ordered by `published_at DESC NULLS LAST` instead of
  `fetched_at`
- `articles.topic` (plain string) replaced by `articles.topic_id`
  (FK → `topics.id`, nullable); API responses unchanged — topic name
  resolved via `joinedload` on every article query
- `FeedSyncService.enrich()` loads topics from the repository once per job
  and passes them to the classifier
- `update_article_enrichment()` resolves topic name → `topic_id`
  before writing; articles without a matching topic get `topic_id = NULL`
- `FeedSyncService.sync()` is now a fast path (fetch + store raw,
  < 5 s); LLM enrichment delegated to `enrich_articles_job` — sync
  completes and notifies the browser before any Ollama call is made
- `cli feeds_sync` uses `FeedSyncService` — was one-by-one inline sync
- Embedding dimension corrected 384 → 768 (`nomic-embed-text` actual)
- `embedding_model` and `embedding_dim` moved to `Settings`

#### Removed

- `settings.topics: list[str]` — topic names and descriptions live
  exclusively in the database
- Hardcoded `_TOPIC_DESCRIPTIONS` dict from `classifier.py`
- APScheduler (`apscheduler` dependency) — replaced by ARQ cron job
- `FeedRepository.save_article()` — replaced by `save_articles_bulk`

#### Fixed

- `PgVectorStore.search()`: `topic` metadata serialized raw `TopicORM`
  instead of `topic.name`; caused `PydanticSerializationError` 500 on
  every search request (CORS error was a symptom)
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
