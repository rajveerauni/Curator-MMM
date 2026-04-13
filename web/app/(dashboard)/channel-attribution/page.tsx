"use client";

import { motion } from "framer-motion";

import { useCompanyIntel } from "@/components/company-intel-context";
import { itemVariants, listVariants, pageVariants } from "@/lib/animations";

export default function ChannelAttributionPage() {
  const { data, loading, error, debouncedQuery } = useCompanyIntel();

  if (!debouncedQuery && !loading) {
    return (
      <PageIntro
        title="Channel Attribution"
        subtitle="Load a company in the header to see AI channel assumptions and supporting headlines."
      />
    );
  }

  if (loading && !data) {
    return <PageSkeleton title="Channel Attribution" />;
  }

  if (error) {
    return <PageIntro title="Channel Attribution" subtitle="" error={error} />;
  }

  if (!data) return <PageSkeleton title="Channel Attribution" />;

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-on-surface sm:text-3xl">
          Channel Attribution
        </h1>
        <p className="mt-1 text-sm text-secondary">
          {data.resolvedName} ({data.ticker}) — AI-generated assumptions, not measured media mix.
        </p>
      </header>

      <section className="ghost-border overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6">
        <h2 className="text-lg font-bold text-on-surface">Channel assumptions (AI)</h2>
        {data.insights?.channelAssumptions?.length ? (
          <motion.ul
            variants={listVariants}
            initial="hidden"
            animate="show"
            className="mt-4 space-y-3"
          >
            {data.insights.channelAssumptions.map((x) => (
              <motion.li
                key={x}
                variants={itemVariants}
                className="flex items-start gap-3 text-sm text-secondary"
              >
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/70" />
                <span>{x}</span>
              </motion.li>
            ))}
          </motion.ul>
        ) : (
          <p className="mt-4 text-sm text-outline">
            {data.insightsError ? "AI insights unavailable — try again shortly." : "No channel assumptions available."}
          </p>
        )}
      </section>

      <section className="ghost-border overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6">
        <h2 className="text-lg font-bold text-on-surface">Supporting headlines</h2>
        <motion.ul
          variants={listVariants}
          initial="hidden"
          animate="show"
          className="mt-4 divide-y divide-white/5"
        >
          {data.news.length === 0 ? (
            <li className="py-2 text-sm text-outline">No articles returned.</li>
          ) : (
            data.news.map((n) => (
              <motion.li key={n.link} variants={itemVariants} className="py-3">
                <a
                  href={n.link}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-primary hover:underline"
                >
                  {n.title}
                </a>
                <p className="mt-0.5 text-xs text-outline">
                  {n.source ?? "—"} · {n.publishedAt ?? "—"}
                </p>
              </motion.li>
            ))
          )}
        </motion.ul>
      </section>
    </motion.div>
  );
}

function PageIntro(props: { title: string; subtitle: string; error?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      <h1 className="text-2xl font-bold text-on-surface sm:text-3xl">{props.title}</h1>
      {props.error ? (
        <p className="rounded-xl border border-error/30 bg-error/10 p-4 text-sm text-error">
          {props.error}
        </p>
      ) : (
        <p className="max-w-2xl text-sm text-secondary">{props.subtitle}</p>
      )}
    </motion.div>
  );
}

function PageSkeleton({ title }: { title: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="animate-pulse space-y-4"
    >
      <div className="h-8 w-56 rounded-xl bg-surface-container-highest" />
      <p className="text-sm text-secondary">{title} — loading…</p>
      <div className="h-40 rounded-xl bg-surface-container-low" />
      <div className="h-32 rounded-xl bg-surface-container-low" />
    </motion.div>
  );
}
