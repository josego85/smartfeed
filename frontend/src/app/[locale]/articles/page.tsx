"use client";

import { ArticleCard } from "@/components/articles/ArticleCard";
import { PageSpinner } from "@/components/ui/spinner";
import { useArticles } from "@/hooks/useArticles";
import { getTopicMeta } from "@/lib/topics";
import { Suspense } from "react";
import { useTranslations } from "next-intl";

function ArticlesContent() {
  const t = useTranslations("articles");
  const { articles, isLoading, error, topic, unreadCount } = useArticles();

  const heading = topic ? getTopicMeta(topic).label : t("title");

  if (isLoading) return <PageSpinner />;
  if (error) return <ErrorState />;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-8 flex items-baseline gap-3">
        <h1 className="text-2xl font-bold text-slate-900">{heading}</h1>
        {unreadCount > 0 && (
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
            {unreadCount} {t("unread")}
          </span>
        )}
      </div>

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
  const t = useTranslations("articles");
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-4xl">📭</p>
      <p className="mt-3 text-base font-medium text-slate-700">{t("empty")}</p>
      <p className="mt-1 text-sm text-slate-400">{t("emptyHint")}</p>
    </div>
  );
}

function ErrorState() {
  const t = useTranslations("articles");
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-4xl">⚠️</p>
      <p className="mt-3 text-sm text-slate-500">{t("error")}</p>
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
