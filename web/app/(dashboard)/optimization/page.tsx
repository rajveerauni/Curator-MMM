"use client";

import { motion } from "framer-motion";

import { useCompanyIntel } from "@/components/company-intel-context";
import { itemVariants, listVariants, pageVariants } from "@/lib/animations";

export default function OptimizationPage() {
  const { data, loading, error, debouncedQuery } = useCompanyIntel();

  if (!debouncedQuery && !loading) {
    return (
      <PageIntro
        title="Optimization"
        subtitle="Search for a company to view AI strategic recommendations grounded in live market and news context."
      />
    );
  }

  if (loading && !data) {
    return <PageSkeleton />;
  }

  if (error) {
    return <PageIntro title="Optimization" subtitle="" error={error} />;
  }

  if (!data) return <PageSkeleton />;

  const chgPct = data.stock.regularMarketChangePercent;

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 gap-6 lg:grid-cols-3"
    >
      <div className="space-y-4 lg:col-span-2">
        <header>
          <h1 className="text-2xl font-bold text-on-surface sm:text-3xl">Optimization</h1>
          <p className="mt-1 text-sm text-secondary">
            {data.resolvedName} ({data.ticker})
          </p>
        </header>
        <section className="ghost-border rounded-xl bg-surface-container-low p-4 sm:p-6">
          <h2 className="text-lg font-bold text-on-surface">Strategic recommendations</h2>
          {data.insights?.strategicRecommendations?.length ? (
            <motion.ol
              variants={listVariants}
              initial="hidden"
              animate="show"
              className="mt-4 space-y-3"
            >
              {data.insights.strategicRecommendations.map((x, i) => (
                <motion.li
                  key={x}
                  variants={itemVariants}
                  className="flex items-start gap-3 text-sm text-secondary"
                >
                  <span className="shrink-0 flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary mt-0.5">
                    {i + 1}
                  </span>
                  <span>{x}</span>
                </motion.li>
              ))}
            </motion.ol>
          ) : (
            <p className="mt-4 text-sm text-outline">
              {data.insightsError || "No recommendations yet."}
            </p>
          )}
        </section>
      </div>

      <motion.aside
        initial={{ opacity: 0, x: 16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, delay: 0.15 }}
        className="ghost-border h-fit overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6"
      >
        <h2 className="text-sm font-bold uppercase tracking-wider text-outline">Snapshot</h2>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex justify-between gap-2">
            <dt className="text-secondary">Price</dt>
            <dd className="text-right font-medium text-on-surface">
              {data.stock.regularMarketPrice?.toFixed(2) ?? "—"} {data.stock.currency}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-secondary">Change %</dt>
            <dd
              className={`text-right font-medium ${
                chgPct != null && chgPct >= 0 ? "text-primary" : "text-error"
              }`}
            >
              {chgPct != null ? `${chgPct >= 0 ? "+" : ""}${chgPct.toFixed(2)}%` : "—"}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-secondary">Trend</dt>
            <dd className="text-right text-on-surface capitalize">{data.stock.trendLabel}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-secondary">52w High</dt>
            <dd className="text-right text-on-surface">
              {data.stock.fiftyTwoWeekHigh?.toFixed(2) ?? "—"}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-secondary">52w Low</dt>
            <dd className="text-right text-on-surface">
              {data.stock.fiftyTwoWeekLow?.toFixed(2) ?? "—"}
            </dd>
          </div>
        </dl>
      </motion.aside>
    </motion.div>
  );
}

function PageIntro(props: { title: string; subtitle: string; error?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h1 className="text-2xl font-bold text-on-surface sm:text-3xl">{props.title}</h1>
      {props.error ? (
        <p className="mt-4 rounded-xl border border-error/30 bg-error/10 p-4 text-sm text-error">
          {props.error}
        </p>
      ) : (
        <p className="mt-2 max-w-2xl text-sm text-secondary">{props.subtitle}</p>
      )}
    </motion.div>
  );
}

function PageSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="animate-pulse space-y-4"
    >
      <div className="h-8 w-40 rounded-xl bg-surface-container-highest" />
      <div className="h-56 rounded-xl bg-surface-container-low" />
    </motion.div>
  );
}
