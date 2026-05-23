import { feedsApi } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

export function useAddFeed() {
  const [url, setUrl] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (normalizedUrl: string) => feedsApi.add({ url: normalizedUrl }),
    onSuccess: () => {
      setUrl("");
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    const normalized = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    setUrl(normalized);
    mutation.mutate(normalized);
  };

  return { url, setUrl, handleSubmit, isPending: mutation.isPending };
}
