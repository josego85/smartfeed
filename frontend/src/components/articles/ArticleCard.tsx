"use client";

import { Badge } from "@/components/ui/badge";
import { formatDate, getTopicMeta } from "@/lib/topics";
import { cn } from "@/lib/utils";
import type { Article } from "@/types";
import { ExternalLink, Sparkles } from "lucide-react";
import { articlesApi } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const meta = getTopicMeta(article.topic);
  const queryClient = useQueryClient();

  const handleClick = async () => {
    if (!article.is_read) {
      await articlesApi.markRead(article.id);
      queryClient.invalidateQueries({ queryKey: ["articles"] });
    }
  };

  return (
    <article
      className={cn(
        "group relative flex flex-col gap-3 rounded-xl border p-5 transition-all duration-200",
        "hover:shadow-md hover:-translate-y-0.5",
        article.is_read
          ? "border-slate-100 bg-white"
          : "border-slate-200 bg-white shadow-sm",
      )}
    >
      {/* Unread indicator */}
      {!article.is_read && (
        <span className="absolute right-4 top-4 h-2 w-2 rounded-full bg-blue-500" />
      )}

      {/* Topic badge */}
      <div className="flex items-center gap-2">
        <Badge className={meta.color}>{meta.label}</Badge>
      </div>

      {/* Title */}
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={handleClick}
        className={cn(
          "line-clamp-2 text-base font-semibold leading-snug transition-colors",
          "group-hover:text-blue-600",
          article.is_read ? "text-slate-500" : "text-slate-900",
        )}
      >
        {article.title}
      </a>

      {/* AI Summary */}
      {article.summary && (
        <div className="flex gap-2 rounded-lg bg-slate-50 px-3 py-2.5">
          <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-purple-400" />
          <p className="line-clamp-3 text-xs leading-relaxed text-slate-600">{article.summary}</p>
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto flex items-center justify-between text-xs text-slate-400">
        <span>{formatDate(article.published_at ?? article.fetched_at)}</span>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={handleClick}
          className="flex items-center gap-1 rounded-md px-2 py-1 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          Read <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </article>
  );
}
