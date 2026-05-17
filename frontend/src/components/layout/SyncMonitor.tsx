"use client";

import { BASE_URL, SYNC_DISPLAY_MS, TERMINAL_STATUSES } from "@/lib/constants";
import { useSyncContext } from "@/contexts/sync";
import { feedsApi } from "@/lib/api";
import type { SyncJobStatus } from "@/types";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

export function SyncMonitor() {
  const { jobs, updateJob, removeJob } = useSyncContext();
  const queryClient = useQueryClient();

  const jobsRef = useRef(jobs);
  const actionsRef = useRef({ updateJob, removeJob, queryClient });

  useEffect(() => {
    jobsRef.current = jobs;
  }, [jobs]);
  useEffect(() => {
    actionsRef.current = { updateJob, removeJob, queryClient };
  });

  useEffect(() => {
    const settle = (payload: SyncJobStatus) => {
      const { updateJob, removeJob, queryClient } = actionsRef.current;
      updateJob(payload.job_id, {
        status: payload.status,
        result: payload.result,
        error: payload.error,
      });
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      setTimeout(() => removeJob(payload.job_id), SYNC_DISPLAY_MS);
    };

    // One-time HTTP check for jobs recovered from localStorage after a page refresh
    jobsRef.current
      .filter((j) => !TERMINAL_STATUSES.has(j.status))
      .forEach(async (job) => {
        try {
          const res = await feedsApi.syncStatus(job.feedId, job.jobId);
          if (TERMINAL_STATUSES.has(res.status)) settle(res);
        } catch {
          /* ignore */
        }
      });

    // SSE: server pushes one event when the job finishes — no polling
    const es = new EventSource(`${BASE_URL}/api/feeds/sync-events`);
    es.onmessage = (event) => {
      try {
        const payload: SyncJobStatus = JSON.parse(event.data);
        if (payload.job_id) settle(payload);
      } catch {
        /* SSE ping or malformed — ignore */
      }
    };

    return () => es.close();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps — stable via refs

  return null;
}
