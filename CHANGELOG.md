# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) —
[Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Backend

#### Added

- `FeedStatus` enum (`active`, `forbidden`, `not_found`, `unreachable`) in
  `core/models.py`; `status` and `last_error` fields on `Feed`
- `FeedRepository.update_feed_status()` abstract method + `PostgresRepository`
  implementation; idempotent migration adds `status VARCHAR(20)` and `last_error TEXT`
  columns to existing DBs
- `PermanentFetchError` / `TransientFetchError` exception hierarchy in
  `ingestion/fetcher.py`; `UnsupportedProtocol` (bare URL, no scheme) mapped to
  permanent error
- Browser HTTP headers in `fetch_feed` (`User-Agent`, `Accept`, `Accept-Encoding`,
  `Cache-Control`) to reduce false 403s
- `_SKIP_STATUSES` in `sync_all_feeds_job` — feeds with `forbidden` or `not_found`
  status are skipped on every cron tick (no infinite retry)
- `@field_validator("url")` on `FeedCreate` — rejects URLs without `http://` /
  `https://` at the API layer
- Three-tier test pyramid: **unit** (all I/O mocked), **integration** (FastAPI
  `TestClient` + `dependency_overrides`), **e2e** (real PostgreSQL)
- 193 tests; unit + integration run in < 1 s with no external services
- `tests/unit/` — covers `core/models`, `core/config`, `ingestion/fetcher`,
  `processing/classifier`, `processing/summarizer`, `processing/embeddings`,
  `services/sync_service`; `respx` mocks all `httpx` calls, `AsyncMock` mocks
  `litellm.acompletion`
- `tests/integration/api/` — `test_feeds`, `test_articles`, `test_search`,
  `test_topics`, `test_health`; no Docker, no real DB
- `tests/e2e/storage/test_repository.py` — `FeedRepository` contract tests
  against a real `pgvector` DB; fixture typed as `FeedRepository` (DIP), not
  `PostgresRepository`, so any future adapter replacement requires zero test changes
- `backend/docker-compose.test.yml` — isolated `pgvector/pgvector:pg17` on
  port **5433** (offset from dev) so both stacks run simultaneously;
  `TEST_DATABASE_URL` env var overrides the URL for CI
- `pytest-cov`, `pytest-mock`, `respx` added to `[dependency-groups] dev`
- `pytest.ini_options`: `addopts = "--tb=short -q"`, `e2e` marker excluded by
  default (`-m 'not e2e'`) so CI never requires Docker
- `FetchResult` dataclass in `ingestion/fetcher.py` — wraps feed-level `title` and
  `description` alongside the article list; `fetch_feed` return type changed from
  `list[Article]` to `FetchResult` (covers both RSS `description` and Atom `subtitle`)
- `FeedRepository.update_feed_metadata()` abstract method + `PostgresRepository`
  implementation — idempotent: only writes when the stored field is empty, preserving
  any future manual edits
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

- `sync_feed_job` catches `PermanentFetchError` and returns cleanly so ARQ does not
  schedule a retry; transient errors are re-raised to preserve retry behaviour
- `list_articles()` and `get_article()` filter `is_deleted = FALSE` —
  deleted articles are invisible to all API consumers
- `get_existing_urls()` intentionally does **not** filter deleted articles —
  ensures deleted URLs are never re-fetched on sync

#### Fixed

- Feeds returning 403 / 404 / 410 / 451 no longer retry on every cron cycle —
  permanently blocked feeds are marked and skipped
- Feed title stored as empty string after `POST /feeds/` — `FeedSyncService.sync()` now
  calls `update_feed_metadata` on the first successful sync, populating title and
  description from the RSS/Atom channel element
- 20 ruff lint errors resolved across 14 files: import ordering (I001),
  lines over 100 chars (E501), `timezone.utc` → `datetime.UTC` (UP017),
  unused imports in `database.py`, `test_config.py`, `test_fetcher.py` (F401),
  and unused variable `saved` in `test_repository.py` (F841)
- ruff format applied to 23 unformatted files (consistent style across
  all production and test code)

#### Security

- `idna` bumped 3.13 → 3.16 (CVE-2026-45409) — transitive via `anyio` / `httpx`
- `starlette` bumped 1.0.0 → 1.1.0 (PYSEC-2026-161) — transitive via `fastapi`
- `urllib3` bumped 2.6.3 → 2.7.0 (PYSEC-2026-141, PYSEC-2026-142) — transitive
  via `requests` ← `litellm`; only `uv.lock` updated, `pyproject.toml` unchanged
- `litellm` bumped 1.83.14 → 1.84.0 (PYSEC-2026-388); `pydantic-settings` bumped
  2.14.0 → 2.14.2 (GHSA-4xgf-cpjx-pc3j); `aiohttp` bumped 3.13.4 → 3.14.1
  (11 CVEs, transitive via `litellm`) — resolves all findings from `pip-audit`

---

### Frontend

#### Added

- Status badges (`Forbidden`, `Not Found`, `Unreachable`) on feed list row with
  `title` tooltip showing `last_error`; `FeedStatus` type + `status` / `last_error`
  fields added to `types/index.ts`
- `SourceLabel` component in `ArticleCard` footer — Google favicon service + domain
  name, `Rss` icon as fallback on error; layout: `[favicon] domain · date`
- i18n keys `statusForbidden`, `statusNotFound`, `statusUnreachable` in EN / ES / DE
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

- `useAddFeed` URL normalization: bare domain (e.g. `wired.com/feed/rss`) gets
  `https://` prepended before `mutation.mutate()` — fixed React async state race
  where `setUrl` update wasn't reflected in the closure
- Production build crashes with `useContext` error when `NODE_ENV=development` is inherited
  from the dev container — `NODE_ENV=production` now forced in `package.json` build script
  and `Dockerfile` builder stage
- `middleware.ts` → `proxy.ts`: Next.js 16 deprecates the `middleware` file convention
- `[locale]` layout marked `export const dynamic = "force-dynamic"` — pages that fetch
  live API data must not be statically prerendered
- `LanguageSwitcher` `<button>` missing `type="button"` — could accidentally submit a parent form
- Biome lint: `useNamingConvention` disabled for `src/types/**` — snake_case mirrors the
  backend JSON contract
- `next-env.d.ts` routes reference updated from `.next/types/` → `.next/dev/types/` —
  auto-generated by Next.js 16 dev server

#### Security

- `next` bumped 16.2.4 → 16.2.6 (GHSA-8h8q-6873-q5fj, GHSA-26hh-7cqf-hhc6,
  GHSA-mg66-mrh9-m8jx, GHSA-c4j6-fc7j-m34r, GHSA-492v-c6pp-mqqv,
  GHSA-267c-6grr-h53f, GHSA-36qx-fr4f-26g5) — DoS via Server Components,
  Middleware bypass, SSRF via WebSocket upgrades; 7 high-severity CVEs resolved
- `next-intl` bumped to `^4.12.0` (GHSA-r27j-894h-3w3p) — transitive
  `icu-minify@<=4.9.1` prototype-key DoS in `select` formatters with
  `precompile: true`; patched in `icu-minify@4.9.2` bundled by `next-intl@4.12.0`
- `@vitejs/plugin-react` bumped 4.x → `^5.2.0`; `pnpm.overrides`:
  `vite >= 6.4.2` (GHSA-4w7w-66w2-5vf9 path traversal + GHSA-67mh-4wv8-2f99
  esbuild dev-server CORS) and `postcss >= 8.5.10` (GHSA-qx2v-qp2m-jg93 XSS
  via unescaped `</style>` in stringify output) — all transitive; no
  `package.json` direct-dep changes beyond the version constraints

---

### Infrastructure

#### Added

- GitHub Actions CI for **Backend** (`.github/workflows/ci-backend.yml`) — lint (ruff
  check + format) and unit + integration tests run in parallel on every PR; e2e tests
  against a real `pgvector/pgvector:pg17` service container execute on push to `main`
  only; `uv sync --frozen` ensures reproducible builds; uv lock-file cache keyed on
  `uv.lock`; coverage report uploaded as artifact
- GitHub Actions CI for **Frontend** (`.github/workflows/ci-frontend.yml`) — Biome
  (`biome ci`, read-only), TypeScript type check, and Vitest (`vitest run`) run in
  parallel on every PR; production `next build` gates on all three passing; `.next/cache`
  cached between runs; `pnpm install --frozen-lockfile` for reproducibility
- GitHub Actions **Security** workflow (`.github/workflows/security.yml`) — CodeQL SAST
  for Python and TypeScript (`security-and-quality` query suite), `pip-audit` via `uvx`
  against exported production requirements, `pnpm audit --audit-level=high`; triggers on
  push to `main`, pull requests, and weekly cron (Monday 03:00 UTC)
- **Dependabot** (`.github/dependabot.yml`) — configured for `pip` (backend), `npm`
  (frontend), and `github-actions` (workflow files); weekly schedule, minor/patch
  dev-deps grouped into a single PR to reduce noise
- All action refs **SHA-pinned** to exact commit hashes for supply chain security;
  version tag preserved as inline comment; Dependabot manages future SHA bumps
- `frontend/.nvmrc` — Node.js 22 LTS declared as canonical runtime; read by
  `actions/setup-node` in CI
- `concurrency` groups with `cancel-in-progress: true` on PRs — stale runs cancelled
  automatically to avoid wasted CI minutes

- `frontend/.gitignore` and `frontend/.dockerignore` — exclude `.pnpm-store/` (320 MB),
  `node_modules/`, and `.next/` from git tracking and Docker build context
- `docker-compose.override.yml` backend and worker services: `./backend/src` mounted
  at `/app/src` — source changes reflect instantly without rebuild, matching the
  frontend live-reload pattern
- Husky `9.1.7` git hooks — `pre-commit` runs ruff + biome only on staged Python/TS
  files; `pre-push` runs backend unit + integration tests and `pnpm type-check`;
  installed in `frontend/devDependencies` with `prepare` script activating hooks at
  repo root — no root-level `package.json` needed

#### Fixed

- `python:3.12-slim` ships without system CA certificates; `httpx`/`anyio` TLS handshake
  failed silently with `ConnectError` for all HTTPS feeds in Docker — added
  `apt-get install ca-certificates` to `backend/Dockerfile`
- `pip-audit` in security workflow failed with editable-install hash error — added
  `--no-emit-project` to `uv export` so only third-party deps with hashes are passed
- `pnpm/action-setup@v6` requires an explicit pnpm version; added
  `"packageManager": "pnpm@10.11.0"` to `frontend/package.json` as the single
  source of truth (read automatically by the action, Corepack, and Renovate)

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
