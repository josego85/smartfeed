"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { TERMINAL_STATUSES } from "@/lib/constants";
import type { SyncResult, SyncStatus } from "@/types";

export interface SyncJob {
  feedId: number;
  feedTitle: string;
  jobId: string;
  status: SyncStatus;
  result?: SyncResult;
  error?: string;
}

interface SyncContextValue {
  jobs: SyncJob[];
  addJob: (feedId: number, feedTitle: string, jobId: string) => void;
  updateJob: (jobId: string, patch: Partial<Pick<SyncJob, "status" | "result" | "error">>) => void;
  removeJob: (jobId: string) => void;
}

const STORAGE_KEY = "smartfeed:sync-jobs";

function loadJobs(): SyncJob[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

const SyncContext = createContext<SyncContextValue | null>(null);

export function SyncProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<SyncJob[]>([]);

  // Load from localStorage only after hydration to avoid SSR mismatch
  useEffect(() => {
    setJobs(loadJobs());
  }, []);

  // Persist only active jobs — terminal ones are ephemeral UI feedback
  useEffect(() => {
    const active = jobs.filter((j) => !TERMINAL_STATUSES.has(j.status));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(active));
  }, [jobs]);

  const addJob = useCallback((feedId: number, feedTitle: string, jobId: string) => {
    setJobs((prev) => {
      const without = prev.filter((j) => j.feedId !== feedId);
      return [...without, { feedId, feedTitle, jobId, status: "queued" }];
    });
  }, []);

  const updateJob = useCallback(
    (jobId: string, patch: Partial<Pick<SyncJob, "status" | "result" | "error">>) => {
      setJobs((prev) => prev.map((j) => (j.jobId === jobId ? { ...j, ...patch } : j)));
    },
    [],
  );

  const removeJob = useCallback((jobId: string) => {
    setJobs((prev) => prev.filter((j) => j.jobId !== jobId));
  }, []);

  return (
    <SyncContext.Provider value={{ jobs, addJob, updateJob, removeJob }}>
      {children}
    </SyncContext.Provider>
  );
}

export function useSyncContext(): SyncContextValue {
  const ctx = useContext(SyncContext);
  if (!ctx) throw new Error("useSyncContext must be used within SyncProvider");
  return ctx;
}

export function useFeedSyncJob(feedId: number): SyncJob | undefined {
  const { jobs } = useSyncContext();
  return jobs.find((j) => j.feedId === feedId);
}
