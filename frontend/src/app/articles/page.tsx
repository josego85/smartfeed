"use client";

import { ArticleCard } from "@/components/articles/ArticleCard";
import { PageSpinner } from "@/components/ui/spinner";
import { articlesApi } from "@/lib/api";
import { getTopicMeta } from "@/lib/topics";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function ArticlesContent() {
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic") ?? undefined;

  const { data: articles, isLoading, error } = useQuery({
    queryKey: ["articles", topic],
    queryFn: () => articlesApi.list({ topic, limit: 100 }),
  });

  const heading = topic ? getTopicMeta(topic).label : "All Articles";
  const unreadCount = articles?.filter((a) => !a.is_read).length ?? 0;

  if (isLoading) return <PageSpinner />;
  if (error) return <ErrorState />;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex items-baseline gap-3">
        <h1 className="text-2xl font-bold text-slate-900">{heading}</h1>
        {unreadCount > 0 && (
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
            {unreadCount} unread
          </span>
        )}
      </div>

      {/* Articles grid */}
      {articles?.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {articles?.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-4xl">📭</p>
      <p className="mt-3 text-base font-medium text-slate-700">No articles yet</p>
      <p className="mt-1 text-sm text-slate-400">
        Add some feeds and sync them to see articles here.
      </p>
    </div>
  );
}

function ErrorState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-4xl">⚠️</p>
      <p className="mt-3 text-sm text-slate-500">Could not load articles. Is the backend running?</p>
    </div>
  );
}

export default function ArticlesPage() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <ArticlesContent />
    </Suspense>
  );
}
