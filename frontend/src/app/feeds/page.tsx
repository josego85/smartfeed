"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageSpinner, Spinner } from "@/components/ui/spinner";
import { feedsApi } from "@/lib/api";
import type { Feed } from "@/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, RefreshCw, Rss, Trash2 } from "lucide-react";
import { useState } from "react";

function FeedRow({ feed }: { feed: Feed }) {
  const queryClient = useQueryClient();

  const syncMutation = useMutation({
    mutationFn: () => feedsApi.sync(feed.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["articles"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => feedsApi.delete(feed.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feeds"] }),
  });

  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
        <Rss className="h-5 w-5 text-slate-500" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-900">
          {feed.title || "Untitled feed"}
        </p>
        <p className="truncate text-xs text-slate-400">{feed.url}</p>
      </div>

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          title="Sync feed"
        >
          {syncMutation.isPending ? (
            <Spinner className="h-3.5 w-3.5" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
          {syncMutation.isSuccess ? "Synced!" : "Sync"}
        </Button>

        <Button
          size="sm"
          variant="danger"
          onClick={() => deleteMutation.mutate()}
          disabled={deleteMutation.isPending}
          title="Remove feed"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

function AddFeedForm() {
  const [url, setUrl] = useState("");
  const queryClient = useQueryClient();

  const addMutation = useMutation({
    mutationFn: () => feedsApi.add({ url }),
    onSuccess: () => {
      setUrl("");
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) addMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <Input
        placeholder="https://example.com/feed.xml"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="flex-1"
      />
      <Button
        type="submit"
        variant="primary"
        disabled={!url.trim() || addMutation.isPending}
      >
        {addMutation.isPending ? <Spinner className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        Add Feed
      </Button>
    </form>
  );
}

export default function FeedsPage() {
  const { data: feeds, isLoading, error } = useQuery({
    queryKey: ["feeds"],
    queryFn: feedsApi.list,
  });

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <div className="mb-8">
        <h1 className="mb-1 text-2xl font-bold text-slate-900">Feeds</h1>
        <p className="text-sm text-slate-500">
          Manage your RSS sources. Feeds sync automatically every 30 minutes.
        </p>
      </div>

      {/* Add feed */}
      <div className="mb-8 rounded-xl border border-slate-200 bg-slate-50 p-5">
        <p className="mb-3 text-sm font-medium text-slate-700">Add a new feed</p>
        <AddFeedForm />
      </div>

      {/* Feed list */}
      {isLoading && <PageSpinner />}
      {error && (
        <p className="text-center text-sm text-slate-400">
          Could not load feeds. Is the backend running?
        </p>
      )}

      {feeds && feeds.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-4xl">📡</p>
          <p className="mt-3 text-sm text-slate-400">No feeds yet. Add one above to get started.</p>
        </div>
      )}

      {feeds && feeds.length > 0 && (
        <div className="flex flex-col gap-3">
          {feeds.map((feed) => (
            <FeedRow key={feed.id} feed={feed} />
          ))}
        </div>
      )}
    </div>
  );
}
