import { Sidebar } from "@/components/layout/Sidebar";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SmartFeed",
  description: "Personal RSS reader with AI summaries and semantic search",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-white`}>
        <Providers>
          <div className="flex h-screen overflow-hidden">
            <Suspense>
              <Sidebar />
            </Suspense>
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
