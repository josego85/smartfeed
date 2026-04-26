"use client";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { searchApi } from "@/lib/api";
import { formatDate, getTopicMeta } from "@/lib/topics";
import type { SearchResult } from "@/types";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Search, Sparkles } from "lucide-react";
import { useCallback, useState } from "react";

function SearchResultCard({ result }: { result: SearchResult }) {
  const meta = getTopicMeta(result.metadata.topic);
  const score = Math.round(result.score * 100);

  return (
    <a
      href={result.metadata.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <Badge className={meta.color}>{meta.label}</Badge>
        <span className="flex items-center gap-1 text-xs text-slate-400">
          <Sparkles className="h-3 w-3 text-purple-400" />
          {score}% match
        </span>
      </div>

      <p className="line-clamp-2 text-base font-semibold text-slate-900 group-hover:text-blue-600">
        {result.metadata.title}
      </p>

      <p className="line-clamp-3 text-xs leading-relaxed text-slate-500">{result.document}</p>

      <div className="flex items-center justify-end text-xs text-slate-400">
        <span className="flex items-center gap-1">
          Read <ExternalLink className="h-3 w-3" />
        </span>
      </div>
    </a>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    clearTimeout((window as any).__searchTimer);
    (window as any).__searchTimer = setTimeout(() => setDebouncedQuery(val), 400);
  }, []);

  const { data: results, isLoading } = useQuery({
    queryKey: ["search", debouncedQuery],
    queryFn: () => searchApi.semantic(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-8">
        <h1 className="mb-1 text-2xl font-bold text-slate-900">Semantic Search</h1>
        <p className="text-sm text-slate-500">
          Search by meaning, not just keywords. Ask questions in plain language.
        </p>
      </div>

      <Input
        icon={<Search className="h-4 w-4" />}
        placeholder='e.g. "how does RLHF work" or "kubernetes cost optimization"'
        value={query}
        onChange={handleChange}
        className="mb-8 py-3 text-base"
        autoFocus
      />

      {isLoading && (
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <Spinner />
          Searching...
        </div>
      )}

      {!isLoading && results && results.length === 0 && (
        <div className="py-16 text-center text-slate-400">No results found for "{debouncedQuery}"</div>
      )}

      {!isLoading && results && results.length > 0 && (
        <>
          <p className="mb-4 text-sm text-slate-500">{results.length} results</p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {results.map((r) => (
              <SearchResultCard key={r.article_id} result={r} />
            ))}
          </div>
        </>
      )}

      {!query && (
        <div className="py-16 text-center">
          <p className="text-4xl">🔍</p>
          <p className="mt-3 text-sm text-slate-400">
            Type at least 2 characters to start searching
          </p>
        </div>
      )}
    </div>
  );
}
