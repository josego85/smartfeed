export type FeedStatus = "active" | "forbidden" | "not_found" | "unreachable";

export interface Feed {
  id: number;
  url: string;
  title: string;
  description: string;
  created_at: string;
  last_synced_at: string | null;
  status: FeedStatus;
  last_error: string | null;
}

export interface Article {
  id: number;
  feed_id: number;
  url: string;
  title: string;
  content: string;
  summary: string;
  topic: string;
  published_at: string | null;
  fetched_at: string;
  is_read: boolean;
}

export interface SearchResult {
  article_id: string;
  score: number;
  document: string;
  metadata: {
    title: string;
    topic: string;
    url: string;
  };
}

export interface FeedCreate {
  url: string;
  title?: string;
  description?: string;
}

export interface SyncResult {
  feed_id: number;
  fetched: number;
  new: number;
  skipped: number;
}

export type SyncStatus = "queued" | "in_progress" | "complete" | "failed" | "not_found";

export interface SyncJobStatus {
  job_id: string;
  status: SyncStatus;
  result?: SyncResult;
  error?: string;
}
