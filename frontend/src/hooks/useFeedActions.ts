import { feedsApi } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useFeedActions(feedId: number) {
  const queryClient = useQueryClient();

  const sync = useMutation({
    mutationFn: () => feedsApi.sync(feedId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["articles"] }),
  });

  const remove = useMutation({
    mutationFn: () => feedsApi.delete(feedId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feeds"] }),
  });

  return { sync, remove };
}
