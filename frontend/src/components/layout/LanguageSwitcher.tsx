"use client";

import { cn } from "@/lib/utils";
import { usePathname, useRouter } from "@/navigation";
import { useLocale } from "next-intl";

const LANGUAGES = [
  { code: "en", flag: "🇬🇧", label: "English", short: "EN" },
  { code: "es", flag: "🇪🇸", label: "Espanol", short: "ES" },
  { code: "de", flag: "🇩🇪", label: "Deutsch", short: "DE" },
] as const;

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  function switchLocale(code: string) {
    router.replace(pathname, { locale: code });
  }

  return (
    <div className="flex rounded-xl bg-slate-100 p-1">
      {LANGUAGES.map((lang) => {
        const isActive = lang.code === locale;
        return (
          <button
            key={lang.code}
            onClick={() => switchLocale(lang.code)}
            title={lang.label}
            className={cn(
              "relative flex flex-1 flex-col items-center gap-0.5 rounded-lg py-2 text-center transition-all duration-200",
              isActive ? "bg-white shadow-sm" : "hover:bg-slate-50",
            )}
          >
            <span className="text-base leading-none">{lang.flag}</span>
            <span
              className={cn(
                "text-[10px] font-semibold leading-none tracking-wide transition-colors",
                isActive ? "text-slate-900" : "text-slate-400",
              )}
            >
              {lang.short}
            </span>
            {isActive && (
              <span className="absolute bottom-1 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-blue-500" />
            )}
          </button>
        );
      })}
    </div>
  );
}
