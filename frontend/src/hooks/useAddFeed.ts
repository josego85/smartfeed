import { feedsApi } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

export function useAddFeed() {
  const [url, setUrl] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => feedsApi.add({ url }),
    onSuccess: () => {
      setUrl("");
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) mutation.mutate();
  };

  return { url, setUrl, handleSubmit, isPending: mutation.isPending };
}
