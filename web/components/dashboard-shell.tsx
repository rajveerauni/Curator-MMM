"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useCompanyIntel } from "@/components/company-intel-context";
import { SearchAutocomplete } from "@/components/search-autocomplete";
import { DASHBOARD_NAV } from "@/lib/nav-config";

function navClass(active: boolean) {
  if (active) {
    return "relative flex items-center gap-4 border-r-2 border-primary bg-white/5 px-4 py-3 text-sm font-bold text-primary transition-colors";
  }
  return "relative flex items-center gap-4 px-4 py-3 text-sm text-secondary opacity-80 transition-colors hover:bg-white/5 hover:opacity-100";
}

export default function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { query, setQuery, loading, exportMessage, clearExportMessage } = useCompanyIntel();

  return (
    <div className="flex h-[100dvh] w-full max-w-[100vw] overflow-hidden bg-background text-on-background">
      {/* Sidebar */}
      <aside className="hidden h-full w-64 shrink-0 flex-col overflow-y-auto overflow-x-hidden border-r border-white/10 bg-[#0b1326] py-6 md:flex">
        <div className="mb-8 flex items-center gap-3 px-6">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary-container"
          >
            <span className="material-symbols-outlined text-lg text-on-primary-container">
              analytics
            </span>
          </motion.div>
          <div className="min-w-0">
            <Link href="/" className="block">
              <h1 className="text-xl font-bold tracking-tighter text-[#008080]">Curator MMM</h1>
            </Link>
            <p className="text-[10px] uppercase tracking-widest text-secondary opacity-70">
              Marketing Insights
            </p>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-3 pb-4">
          {DASHBOARD_NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link key={item.href} href={item.href} className={navClass(active)} prefetch>
                {active && (
                  <motion.span
                    layoutId="sidebar-active-pill"
                    className="absolute inset-0 rounded-lg bg-primary/10"
                    transition={{ type: "spring", stiffness: 400, damping: 35 }}
                  />
                )}
                <span className="relative material-symbols-outlined shrink-0" style={active ? { fontVariationSettings: "'FILL' 1" } : undefined}>{item.icon}</span>
                <span className="relative min-w-0 truncate tracking-tight">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main panel */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <header className="sticky top-0 z-40 flex h-16 w-full min-w-0 shrink-0 items-center justify-between gap-4 border-b border-white/5 bg-background/80 px-4 shadow-lg shadow-black/20 backdrop-blur-xl sm:px-6 lg:px-8">
          <div className="flex min-w-0 flex-1 items-center gap-4 lg:gap-8">
            <span className="hidden shrink-0 text-base font-black uppercase tracking-tight text-white sm:inline lg:text-lg">
              Marketing Curator
            </span>
            <SearchAutocomplete
              value={query}
              onChange={setQuery}
              loading={loading}
              clearExportMessage={clearExportMessage}
            />
          </div>
          <div className="flex shrink-0 items-center gap-3 sm:gap-6">
            <button
              type="button"
              className="hidden text-[#adc7ff] transition-opacity hover:opacity-80 sm:block"
              aria-label="Calendar"
            >
              <span className="material-symbols-outlined">calendar_today</span>
            </button>
            <button
              type="button"
              className="relative hidden text-[#adc7ff] transition-opacity hover:opacity-80 sm:block"
              aria-label="Notifications"
            >
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute right-0 top-0 h-2 w-2 rounded-full border-2 border-background bg-error" />
            </button>
          </div>
        </header>

        {/* Progress bar */}
        <AnimatePresence>
          {loading ? (
            <motion.div
              key="progress"
              initial={{ scaleX: 0, opacity: 1 }}
              animate={{ scaleX: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1.2, ease: "easeInOut" }}
              style={{ transformOrigin: "left" }}
              className="h-[3px] w-full shrink-0 bg-gradient-to-r from-primary/40 via-primary to-primary/40"
              role="progressbar"
              aria-valuetext="Loading"
            />
          ) : (
            <div className="h-[3px] shrink-0 bg-transparent" aria-hidden />
          )}
        </AnimatePresence>

        {/* Export message */}
        <AnimatePresence>
          {exportMessage && (
            <motion.div
              key="export-msg"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="shrink-0 overflow-hidden border-b border-amber-500/30 bg-amber-500/10"
            >
              <div className="px-4 py-2 text-center text-sm text-amber-100 sm:px-8" role="status">
                {exportMessage}
                <button
                  type="button"
                  className="ml-2 underline hover:no-underline"
                  onClick={clearExportMessage}
                >
                  Dismiss
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <main className="min-h-0 min-w-0 flex-1 overflow-y-auto overflow-x-hidden">
          <div className="mx-auto w-full max-w-[1600px] px-4 pb-24 pt-6 sm:px-6 sm:pb-8 lg:px-8">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-[100] flex h-14 items-stretch justify-around gap-1 overflow-x-auto border-t border-white/5 bg-surface-container-highest/95 px-1 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl md:hidden">
        {DASHBOARD_NAV.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`relative flex min-w-[3.5rem] flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1 ${
                active ? "text-primary" : "text-secondary opacity-70"
              }`}
              prefetch
            >
              {active && (
                <motion.span
                  layoutId="mobile-active-pill"
                  className="absolute inset-x-1 top-1 h-1 rounded-full bg-primary/60"
                  transition={{ type: "spring", stiffness: 500, damping: 40 }}
                />
              )}
              <span
                className="material-symbols-outlined text-[22px]"
                style={active ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                {item.icon}
              </span>
              <span className={`max-w-full truncate text-[9px] ${active ? "font-bold" : ""}`}>
                {item.label.split(" ")[0]}
              </span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
