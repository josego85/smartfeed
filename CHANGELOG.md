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
- Zero-shot topic classifier via sentence-transformer embeddings against rich keyword descriptions (no labeled training data)
- RSS/Atom ingestion with browser `User-Agent` header to avoid 403 rejections
- APScheduler background sync: fetch → classify → summarize → embed pipeline
- LLM summarization via `litellm` — Ollama by default, Claude/OpenAI/OpenRouter via single env var swap
- Typer CLI for ops: `feeds_add`, `feeds_list`, `feeds_sync`, `search`

---

### Frontend

#### Added

- Next.js 15 App Router with `shadcn/ui` and Tailwind CSS v4
- Feed management: add, list, sync, delete
- Article listing with topic filter and read/unread tracking
- Semantic search view with ranked results and similarity score
- TanStack Query for server state management and background refetching

---

### Infrastructure

#### Added

- Docker Compose: `pgvector/pgvector:pg17`, named volume `pgdata`, backend startup gated on DB healthcheck
