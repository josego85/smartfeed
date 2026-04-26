# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) — [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

### Backend

#### Added

- FastAPI REST API: feeds CRUD, article listing with topic/feed filters, semantic search
- PostgreSQL + pgvector as unified storage: relational data and `Vector(384)` embeddings in one DB
- `PostgresRepository` and `PgVectorStore` implementing `core/` interfaces — swappable without touching business logic
- Zero-shot classifier via async Ollama embeddings (`nomic-embed-text`) — keyword
  descriptions, no labeled training data needed
- RSS/Atom ingestion with browser `User-Agent` header to avoid 403 rejections
- APScheduler background sync: fetch → classify → summarize → embed pipeline
- LLM summarization via `litellm` — Ollama by default, Claude/OpenAI/OpenRouter via single env var swap
- Typer CLI for ops: `feeds_add`, `feeds_list`, `feeds_sync`, `search`
- Embeddings and LLM unified via Ollama (eliminates torch/sentence-transformers
  2GB+ dependency, 5-10 min Docker builds)
- Dependency pinning with exact versions (security, reproducibility, and faster
  builds)

---

### Frontend

#### Added

- Next.js 15 App Router with `shadcn/ui` and Tailwind CSS v4
- Feed management: add, list, sync, delete
- Article listing with topic filter and read/unread tracking
- Semantic search view with ranked results and similarity score
- TanStack Query for server state management and background refetching
- i18n via `next-intl`: English, Spanish (ES), and German with
  SEO-friendly locale-prefixed routes (`/en/`, `/es/`, `/de/`)
- `LanguageSwitcher` segmented-control component (flag + code,
  iOS-style, placed at top of sidebar) for locale switching
- Translation message files (`messages/en.json`, `es.json`, `de.json`)
  covering namespaces: `nav`, `articles`, `feeds`, `search`, `metadata`

#### Changed

- Routes moved under `src/app/[locale]/` — middleware auto-detects
  and redirects to the preferred locale
- `useArticles(topic)` hook extracts data fetching and `unreadCount`
  derivation out of the articles page render
- `useFeedActions(feedId)` hook encapsulates sync and delete mutations
  out of `FeedRow`
- `useAddFeed()` hook encapsulates URL state, mutation, and submit
  handler out of `AddFeedForm`
- `useSearch()` hook extracts debounce logic and semantic query out of
  the search page
- Each component calls its own `useTranslations` — no prop drilling of
  `t`

#### Fixed

- `ArticleCard` "Read" link was hardcoded English — now translated via
  `t("articles.read")` in the active locale
- `formatDate` ignored the active locale — now receives `useLocale()`
  so relative dates render in the correct language

---

### Infrastructure

#### Added

- Docker Compose: `pgvector/pgvector:pg17`, named volume `pgdata`, backend startup gated on DB healthcheck
