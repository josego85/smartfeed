import type { SyncStatus } from "@/types";

export const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const num = (key: string, fallback: number) => Number(process.env[key] || fallback) || fallback;

export const ARTICLES_LIMIT = num("NEXT_PUBLIC_ARTICLES_LIMIT", 100);
export const DEFAULT_SEARCH_RESULTS = num("NEXT_PUBLIC_DEFAULT_SEARCH_RESULTS", 10);
export const MIN_SEARCH_LENGTH = num("NEXT_PUBLIC_MIN_SEARCH_LENGTH", 2);
export const SEARCH_DEBOUNCE_MS = num("NEXT_PUBLIC_SEARCH_DEBOUNCE_MS", 400);
export const QUERY_STALE_MS = num("NEXT_PUBLIC_QUERY_STALE_MS", 30_000);
export const SYNC_DISPLAY_MS = num("NEXT_PUBLIC_SYNC_DISPLAY_MS", 5_000);

export const TERMINAL_STATUSES = new Set<SyncStatus>(["complete", "failed", "not_found"]);
