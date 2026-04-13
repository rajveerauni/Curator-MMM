"use client";

import { motion } from "framer-motion";

import { useCompanyIntel } from "@/components/company-intel-context";
import { itemVariants, listVariants, pageVariants } from "@/lib/animations";

export default function ScenariosPage() {
  const { data, loading, error, debouncedQuery } = useCompanyIntel();

  if (!debouncedQuery && !loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-2xl font-bold text-on-surface sm:text-3xl">Scenarios</h1>
        <p className="mt-2 max-w-2xl text-sm text-secondary">
          Search for a company to view AI-generated key insights and pipeline warnings for that
          snapshot.
        </p>
      </motion.div>
    );
  }

  if (loading && !data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="animate-pulse space-y-4"
      >
        <div className="h-8 w-32 rounded-xl bg-surface-container-highest" />
        <div className="h-48 rounded-xl bg-surface-container-low" />
        <div className="h-32 rounded-xl bg-surface-container-low" />
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-2xl font-bold text-on-surface">Scenarios</h1>
        <p className="mt-4 rounded-xl border border-error/30 bg-error/10 p-4 text-sm text-error">
          {error}
        </p>
      </motion.div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      <header>
        <h1 className="text-2xl font-bold text-on-surface sm:text-3xl">Scenarios</h1>
        <p className="mt-1 text-sm text-secondary">
          {data.resolvedName} ({data.ticker})
        </p>
      </header>


      <section className="ghost-border overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6">
        <h2 className="text-lg font-bold text-on-surface">Key insights</h2>
        {data.insights?.keyInsights?.length ? (
          <motion.ul
            variants={listVariants}
            initial="hidden"
            animate="show"
            className="mt-4 space-y-3"
          >
            {data.insights.keyInsights.map((x) => (
              <motion.li
                key={x}
                variants={itemVariants}
                className="flex items-start gap-3 text-sm text-secondary"
              >
                <span
                  className="material-symbols-outlined mt-0.5 shrink-0 text-sm text-primary"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  auto_awesome
                </span>
                <span>{x}</span>
              </motion.li>
            ))}
          </motion.ul>
        ) : (
          <p className="mt-4 text-sm text-outline">
            {data.insightsError ? "AI insights unavailable — try again shortly." : "No insights loaded."}
          </p>
        )}
      </section>

      {data.insights?.riskNotes?.length ? (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.2 }}
          className="ghost-border overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6"
        >
          <h2 className="text-lg font-bold text-on-surface">Risk notes</h2>
          <motion.ul
            variants={listVariants}
            initial="hidden"
            animate="show"
            className="mt-4 space-y-3"
          >
            {data.insights.riskNotes.map((x) => (
              <motion.li
                key={x}
                variants={itemVariants}
                className="flex items-start gap-3 text-sm text-secondary"
              >
                <span
                  className="material-symbols-outlined mt-0.5 shrink-0 text-sm text-tertiary"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  error
                </span>
                <span>{x}</span>
              </motion.li>
            ))}
          </motion.ul>
        </motion.section>
      ) : null}
    </motion.div>
  );
}
