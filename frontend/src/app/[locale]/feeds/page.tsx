"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageSpinner, Spinner } from "@/components/ui/spinner";
import { useAddFeed } from "@/hooks/useAddFeed";
import { useFeedActions } from "@/hooks/useFeedActions";
import { feedsApi } from "@/lib/api";
import type { Feed, FeedStatus } from "@/types";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle, Loader2, Plus, RefreshCw, Rss, Trash2, XCircle } from "lucide-react";
import { useTranslations } from "next-intl";

const ACTIVE = new Set(["queued", "in_progress"]);

const STATUS_BADGE: Record<
  Exclude<FeedStatus, "active">,
  { labelKey: "statusForbidden" | "statusNotFound" | "statusUnreachable"; className: string }
> = {
  forbidden: { labelKey: "statusForbidden", className: "border-red-200 bg-red-50 text-red-600" },
  not_found: { labelKey: "statusNotFound", className: "border-orange-200 bg-orange-50 text-orange-600" },
  unreachable: { labelKey: "statusUnreachable", className: "border-yellow-200 bg-yellow-50 text-yellow-700" },
};

function SyncButton({ feed }: { feed: Feed }) {
  const t = useTranslations("feeds");
  const { sync, syncJob } = useFeedActions(feed.id, feed.title || feed.url);

  const isSyncing = sync.isPending || (syncJob !== undefined && ACTIVE.has(syncJob.status));
  const isComplete = syncJob?.status === "complete";
  const isFailed = syncJob?.status === "failed";
  const errorTitle = isFailed && syncJob?.error ? syncJob.error : undefined;

  return (
    <Button
      size="sm"
      variant="ghost"
      onClick={() => sync.mutate()}
      disabled={isSyncing}
      title={errorTitle}
    >
      {isSyncing && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
      {isComplete && <CheckCircle className="h-3.5 w-3.5 text-green-500" />}
      {isFailed && <XCircle className="h-3.5 w-3.5 text-red-400" />}
      {!isSyncing && !isComplete && !isFailed && <RefreshCw className="h-3.5 w-3.5" />}
      {isSyncing ? t("syncing") : isComplete ? t("synced") : isFailed ? t("syncFailed") : t("sync")}
    </Button>
  );
}

function FeedRow({ feed }: { feed: Feed }) {
  const t = useTranslations("feeds");
  const { remove } = useFeedActions(feed.id, feed.title || feed.url);

  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
        <Rss className="h-5 w-5 text-slate-500" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-semibold text-slate-900">
            {feed.title || "Untitled feed"}
          </p>
          {feed.status !== "active" && STATUS_BADGE[feed.status] && (
            <Badge
              className={STATUS_BADGE[feed.status].className}
              title={feed.last_error ?? undefined}
            >
              {t(STATUS_BADGE[feed.status].labelKey)}
            </Badge>
          )}
        </div>
        <p className="truncate text-xs text-slate-400">{feed.url}</p>
        {feed.last_synced_at && (
          <p className="text-xs text-slate-400">
            {t("lastSynced", {
              date: new Date(feed.last_synced_at).toLocaleString(),
            })}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <SyncButton feed={feed} />
        <Button
          size="sm"
          variant="danger"
          onClick={() => remove.mutate()}
          disabled={remove.isPending}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

function AddFeedForm() {
  const t = useTranslations("feeds");
  const { url, setUrl, handleSubmit, isPending } = useAddFeed();

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <Input
        placeholder="https://example.com/feed.xml"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="flex-1"
      />
      <Button type="submit" variant="primary" disabled={!url.trim() || isPending}>
        {isPending ? <Spinner className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        {t("add")}
      </Button>
    </form>
  );
}

export default function FeedsPage() {
  const t = useTranslations("feeds");
  const {
    data: feeds,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["feeds"],
    queryFn: feedsApi.list,
  });

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <div className="mb-8">
        <h1 className="mb-1 text-2xl font-bold text-slate-900">{t("title")}</h1>
        <p className="text-sm text-slate-500">{t("subtitle")}</p>
      </div>

      <div className="mb-8 rounded-xl border border-slate-200 bg-slate-50 p-5">
        <p className="mb-3 text-sm font-medium text-slate-700">{t("addLabel")}</p>
        <AddFeedForm />
      </div>

      {isLoading && <PageSpinner />}
      {error && <p className="text-center text-sm text-slate-400">{t("error")}</p>}

      {feeds?.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-4xl">📡</p>
          <p className="mt-3 text-sm text-slate-400">{t("empty")}</p>
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
