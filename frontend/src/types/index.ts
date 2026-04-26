export interface Feed {
  id: number;
  url: string;
  title: string;
  description: string;
  created_at: string;
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
