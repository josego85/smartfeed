"use client";

import { SyncMonitor } from "@/components/layout/SyncMonitor";
import { SyncProvider } from "@/contexts/sync";
import { QUERY_STALE_MS } from "@/lib/constants";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: QUERY_STALE_MS,
            refetchOnWindowFocus: false, // no refetch al hacer click en la ventana
          },
        },
      }),
  );
  return (
    <QueryClientProvider client={queryClient}>
      <SyncProvider>
        <SyncMonitor />
        {children}
      </SyncProvider>
    </QueryClientProvider>
  );
}
