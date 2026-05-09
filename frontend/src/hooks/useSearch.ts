import { MIN_SEARCH_LENGTH, SEARCH_DEBOUNCE_MS } from "@/lib/constants";
import { searchApi } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

export function useSearch() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const handleChange = useCallback((value: string) => {
    setQuery(value);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setDebouncedQuery(value), SEARCH_DEBOUNCE_MS);
  }, []);

  const { data: results, isLoading } = useQuery({
    queryKey: ["search", debouncedQuery],
    queryFn: () => searchApi.semantic(debouncedQuery),
    enabled: debouncedQuery.length >= MIN_SEARCH_LENGTH,
  });

  return { query, debouncedQuery, handleChange, results, isLoading };
}
