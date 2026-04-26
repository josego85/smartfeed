"use client";

import { getTopicMeta, TOPICS } from "@/lib/topics";
import { cn } from "@/lib/utils";
import { BookOpen, Rss, Search, Zap } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

const NAV = [
  { href: "/articles", label: "Articles", icon: BookOpen },
  { href: "/search", label: "Search", icon: Search },
  { href: "/feeds", label: "Feeds", icon: Rss },
];

export function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeTopic = searchParams.get("topic");

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-slate-200 bg-slate-50">
      {/* Logo */}
      <div className="flex items-center gap-2.5 border-b border-slate-200 px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <span className="text-base font-semibold text-slate-900">SmartFeed</span>
      </div>

      <div className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
        {/* Navigation */}
        <nav className="flex flex-col gap-0.5">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-slate-200 text-slate-900"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Topics filter */}
        <div>
          <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Topics
          </p>
          <div className="flex flex-col gap-0.5">
            <Link
              href="/articles"
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                !activeTopic
                  ? "bg-slate-200 font-medium text-slate-900"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
              )}
            >
              <span className="h-2 w-2 rounded-full bg-slate-400" />
              All topics
            </Link>

            {TOPICS.map((topic) => {
              const meta = getTopicMeta(topic);
              const active = activeTopic === topic;
              return (
                <Link
                  key={topic}
                  href={`/articles?topic=${encodeURIComponent(topic)}`}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-slate-200 font-medium text-slate-900"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                  )}
                >
                  <span className={cn("h-2 w-2 shrink-0 rounded-full", meta.dot)} />
                  {meta.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
}
