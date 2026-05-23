import { useFeedSyncJob, useSyncContext } from "@/contexts/sync";
import type { SyncJob } from "@/contexts/sync";
import { feedsApi } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useFeedActions(feedId: number, feedTitle: string) {
  const queryClient = useQueryClient();
  const { addJob } = useSyncContext();
  const syncJob: SyncJob | undefined = useFeedSyncJob(feedId);

  const sync = useMutation({
    mutationFn: () => feedsApi.sync(feedId),
    onSuccess: (data) => addJob(feedId, feedTitle, data.job_id),
  });

  const remove = useMutation({
    mutationFn: () => feedsApi.delete(feedId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feeds"] }),
  });

  return { sync, remove, syncJob };
}
