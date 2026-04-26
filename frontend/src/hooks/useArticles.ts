import { articlesApi } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";

export function useArticles() {
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic") ?? undefined;

  const { data: articles, isLoading, error } = useQuery({
    queryKey: ["articles", topic],
    queryFn: () => articlesApi.list({ topic, limit: 100 }),
  });

  const unreadCount = articles?.filter((a) => !a.is_read).length ?? 0;

  return { articles, isLoading, error, topic, unreadCount };
}
