import { BASE_URL } from "@/lib/constants";
import type { Article, Feed, FeedCreate, SearchResult, SyncJobStatus } from "@/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const feedsApi = {
  list: () => request<Feed[]>("/api/feeds/"),
  add: (body: FeedCreate) =>
    request<Feed>("/api/feeds/", { method: "POST", body: JSON.stringify(body) }),
  sync: (feedId: number) =>
    request<SyncJobStatus>(`/api/feeds/${feedId}/sync`, { method: "POST" }),
  syncStatus: (feedId: number, jobId: string) =>
    request<SyncJobStatus>(`/api/feeds/${feedId}/sync-status?job_id=${encodeURIComponent(jobId)}`),
  delete: (feedId: number) =>
    request<void>(`/api/feeds/${feedId}`, { method: "DELETE" }),
};

export const articlesApi = {
  list: (params?: { feed_id?: number; topic?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams(
      Object.entries(params ?? {})
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)])
    ).toString();
    return request<Article[]>(`/api/articles/${qs ? `?${qs}` : ""}`);
  },
  get: (id: number) => request<Article>(`/api/articles/${id}`),
  markRead: (id: number) => request<void>(`/api/articles/${id}/read`, { method: "PATCH" }),
  delete: (id: number) => request<void>(`/api/articles/${id}`, { method: "DELETE" }),
};

export const searchApi = {
  semantic: (q: string, n = 10) =>
    request<SearchResult[]>(`/api/search/?q=${encodeURIComponent(q)}&n=${n}`),
};
