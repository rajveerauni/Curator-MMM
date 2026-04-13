"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useId, useMemo } from "react";

import { useCompanyIntel } from "@/components/company-intel-context";
import {
  buildPriceChartPaths,
  donutSegments,
  drawdownFromHighPct,
  rangePositionPct,
  trendBarWidth,
  volatilityBarWidth,
} from "@/lib/chartMath";
import { cardVariants, containerVariants, fadeIn } from "@/lib/animations";

function fmtMoney(n: number | null, currency: string) {
  if (n == null || Number.isNaN(n)) return "—";
  return `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${currency}`;
}

function fmtPct(n: number | null) {
  if (n == null || Number.isNaN(n)) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

function fmtCompact(n: number | null) {
  if (n == null || Number.isNaN(n)) return "—";
  return Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n);
}

export default function DashboardHome() {
  const { data, error, loading, debouncedQuery, exportReport, exportMessage } =
    useCompanyIntel();
  const chartGradId = `cg-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;

  const chart = useMemo(
    () => buildPriceChartPaths(data?.stock.series ?? []),
    [data?.stock.series]
  );
  const donut = useMemo(() => donutSegments(data), [data]);
  const dd = data?.stock ? drawdownFromHighPct(data.stock) : null;
  const newsPct = data ? Math.min(100, Math.round((data.news.length / 12) * 100)) : 0;

  const insight1 =
    data?.insights?.keyInsights?.[0] ??
    (data?.insightsError
      ? "AI insights unavailable — try again shortly."
      : "Search for a company to generate AI-powered insights.");
  const insight2 =
    data?.insights?.riskNotes?.[0] ??
    "Headlines are third-party content — verify before acting.";
  const insight3 =
    data?.insights?.strategicRecommendations?.[0] ??
    "Strategic recommendations will appear once a company is loaded.";

  const price = data?.stock.regularMarketPrice ?? null;
  const chgPct = data?.stock.regularMarketChangePercent ?? null;
  const chg = data?.stock.regularMarketChange ?? null;
  const vol = data?.stock.averageVolume ?? null;

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header row */}
      <motion.div
        initial="hidden"
        animate="show"
        variants={fadeIn}
        className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
      >
        <div className="min-w-0">
          <h2 className="text-2xl font-bold tracking-tight text-on-surface sm:text-3xl">
            Data Overview
          </h2>
          <p className="mt-1 text-sm text-secondary">
            {data
              ? `${data.resolvedName} (${data.ticker})`
              : "Search above to load live metrics."}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-3">
          <motion.button
            type="button"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={exportReport}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-br from-primary to-secondary px-5 py-2 text-sm font-bold text-on-primary-fixed shadow-lg shadow-primary/20 transition-opacity hover:opacity-90 disabled:opacity-50"
            disabled={loading}
          >
            <span
              className="material-symbols-outlined text-sm"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              {loading ? "hourglass_top" : "download"}
            </span>
            {exportMessage ? "Exported!" : "Export report"}
          </motion.button>
        </div>
      </motion.div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="rounded-xl border border-error/40 bg-error/10 px-4 py-3 text-sm text-error"
            role="alert"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      <AnimatePresence>
        {!debouncedQuery && !loading && (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-dashed border-white/15 bg-surface-container-low/60 px-4 py-10 text-center text-sm text-secondary sm:px-6"
          >
            Enter a company (e.g.{" "}
            <span className="font-semibold text-primary">Tesla</span>,{" "}
            <span className="font-semibold text-primary">Apple</span>) in the header.
            Export downloads JSON for the loaded snapshot.
          </motion.div>
        )}
      </AnimatePresence>

      {/* Metric cards */}
      <motion.div
        key={data?.ticker ?? "empty"}
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6 xl:grid-cols-4"
      >
        <MetricCard
          label="Last price"
          badge={fmtPct(chgPct)}
          badgeVariant={chgPct != null && chgPct >= 0 ? "primary" : "error"}
          value={fmtMoney(price, data?.stock.currency ?? "USD")}
          sub="vs. prior close (Yahoo)"
          spark="#76d6d5"
          path="M0 15 Q 10 5, 20 12 T 40 8 T 60 14 T 80 5 T 100 2"
        />
        <MetricCard
          label="Daily move"
          badge={chg != null ? `${chg >= 0 ? "+" : ""}${fmtCompact(chg)}` : "—"}
          badgeVariant="primary"
          value={fmtPct(chgPct)}
          sub={`Trend: ${data?.stock.trendLabel ?? "—"}`}
          spark="#76d6d5"
          path="M0 18 Q 20 15, 40 10 T 60 8 T 80 4 T 100 1"
        />
        <MetricCard
          label="Vs 52w high"
          badge={dd != null ? `${dd.toFixed(1)}%` : "—"}
          badgeVariant="error"
          value={dd != null ? `${dd.toFixed(2)}% off high` : "—"}
          sub="Drawdown from 52-week high"
          spark="#ffb4ab"
          path="M0 5 Q 20 10, 40 12 T 60 15 T 80 18 T 100 19"
        />
        <MetricCard
          label="Liquidity / news"
          badge={data ? `${data.news.length} articles` : "—"}
          badgeVariant="neutral"
          value={fmtCompact(vol)}
          sub={`Headline rail: ${newsPct}%`}
          spark="#adc7ff"
          path="M0 10 H 20 L 30 15 L 40 10 L 60 10 L 80 12 L 100 10"
        />
      </motion.div>

      {/* Main grid */}
      <motion.div
        variants={fadeIn}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-12 lg:grid-rows-[auto_auto] lg:gap-6"
      >
        {/* Performance chart */}
        <div className="glass-panel spectra-shadow relative min-h-0 overflow-hidden rounded-xl p-4 sm:p-8 lg:col-span-8 lg:row-span-2">
          <div className="pointer-events-none absolute right-0 top-0 p-4 opacity-10">
            <span
              className="material-symbols-outlined text-7xl sm:text-8xl"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              query_stats
            </span>
          </div>
          <div className="relative z-10 mb-6 flex flex-col gap-4 sm:mb-8 md:flex-row md:items-center md:justify-between">
            <div className="min-w-0">
              <h3 className="text-lg font-bold text-on-surface sm:text-xl">Performance trends</h3>
              <p className="text-sm text-secondary">
                Closes (teal) vs 5D SMA (peach, dashed)
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2 rounded-full border border-white/5 bg-surface-container-lowest/50 p-1">
              <span className="rounded-full bg-primary px-3 py-1.5 text-xs font-bold text-on-primary sm:px-4">
                Live
              </span>
              <span className="truncate rounded-full px-3 py-1.5 text-xs font-medium text-secondary sm:px-4">
                {data?.ticker ?? "—"}
              </span>
            </div>
          </div>
          <div className="relative h-[240px] w-full min-w-0 sm:h-[300px]">
            <div className="absolute inset-0 flex flex-col justify-between">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-px w-full bg-outline-variant/10" />
              ))}
            </div>
            <AnimatePresence mode="wait">
              {chart.lineD ? (
                <motion.svg
                  key={chart.lineD.slice(0, 30)}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.5 }}
                  className="relative z-10 h-full w-full min-w-0"
                  viewBox="0 0 1000 300"
                  preserveAspectRatio="none"
                >
                  <defs>
                    <linearGradient id={chartGradId} x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#76d6d5" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#76d6d5" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  {chart.secondaryD ? (
                    <path
                      d={chart.secondaryD}
                      fill="none"
                      stroke="#ffb692"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                      opacity={0.6}
                    />
                  ) : null}
                  <path d={chart.areaD} fill={`url(#${chartGradId})`} stroke="none" />
                  <path
                    d={chart.lineD}
                    fill="none"
                    stroke="#76d6d5"
                    strokeLinecap="round"
                    strokeWidth="4"
                  />
                </motion.svg>
              ) : (
                <motion.div
                  key="no-chart"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="relative z-10 flex h-full items-center justify-center text-sm text-secondary"
                >
                  No series — search a ticker.
                </motion.div>
              )}
            </AnimatePresence>
            <div className="mt-2 flex justify-between gap-2 text-[10px] font-bold uppercase tracking-widest text-outline">
              <span className="truncate">{chart.startDate}</span>
              <span className="truncate">{chart.midDate}</span>
              <span className="truncate">{chart.endDate}</span>
            </div>
          </div>
        </div>

        {/* Signal distribution */}
        <div className="ghost-border min-h-0 overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6 lg:col-span-4">
          <h3 className="mb-4 text-lg font-bold text-on-surface sm:mb-6">Signal distribution</h3>
          <div className="space-y-4 sm:space-y-5">
            <BarRow
              name="52w range position"
              val={`${data ? rangePositionPct(data.stock) : 0}%`}
              width={data ? rangePositionPct(data.stock) : 0}
              tone="100"
            />
            <BarRow name="Headline coverage" val={`${newsPct}%`} width={newsPct} tone="80" />
            <BarRow
              name="Trend heuristic"
              val={data?.stock.trendLabel ?? "—"}
              width={data ? trendBarWidth(data.stock.trendLabel) : 32}
              tone="60"
            />
            <BarRow
              name="Recent volatility"
              val="Rolling proxy"
              width={data ? volatilityBarWidth(data.stock.series) : 28}
              tone="40"
            />
          </div>
        </div>

        {/* Donut */}
        <div className="ghost-border flex min-h-0 min-w-0 flex-col overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6 lg:col-span-2">
          <h3 className="mb-2 text-sm font-bold text-on-surface">Allocation mix</h3>
          <div className="relative mx-auto my-3 flex aspect-square w-full max-w-[200px] items-center justify-center">
            <svg className="h-full w-full max-h-[180px] -rotate-90" viewBox="0 0 36 36">
              <circle
                cx="18"
                cy="18"
                r="16"
                fill="none"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth="4"
              />
              <circle
                cx="18"
                cy="18"
                r="16"
                fill="none"
                stroke="#76d6d5"
                strokeWidth="4"
                strokeDasharray={`${donut.a} 100`}
              />
              <circle
                cx="18"
                cy="18"
                r="16"
                fill="none"
                stroke="#4a8eff"
                strokeWidth="4"
                strokeDasharray={`${donut.b} 100`}
                strokeDashoffset={-donut.a}
              />
              <circle
                cx="18"
                cy="18"
                r="16"
                fill="none"
                stroke="#ffb692"
                strokeWidth="4"
                strokeDasharray={`${donut.c} 100`}
                strokeDashoffset={-(donut.a + donut.b)}
              />
            </svg>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-lg font-black text-on-surface sm:text-xl">{donut.label}</span>
              <span className="text-[8px] uppercase text-outline">mix</span>
            </div>
          </div>
          <div className="mt-auto flex flex-wrap justify-between gap-2 text-[10px] text-outline">
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" /> Range
            </span>
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-secondary-container" /> News
            </span>
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-tertiary" /> AI
            </span>
          </div>
        </div>

        {/* Model insights */}
        <div id="model-insights" className="ghost-border flex min-h-0 min-w-0 flex-col overflow-hidden rounded-xl bg-surface-container-low p-4 sm:p-6 lg:col-span-2">
          <h3 className="mb-3 text-sm font-bold text-on-surface sm:mb-4">Model insights</h3>
          <div className="flex min-h-0 flex-1 flex-col space-y-3 overflow-y-auto sm:space-y-4">
            <InsightRow icon="auto_awesome" iconClass="text-primary" text={insight1} fill />
            <InsightRow icon="error" iconClass="text-tertiary" text={insight2} fill />
            <InsightRow
              icon="trending_up"
              iconClass="text-secondary-container"
              text={insight3}
            />
          </div>
        </div>
      </motion.div>

      {/* Ambient glow */}
      <div className="pointer-events-none py-6 opacity-20">
        <div className="h-32 rounded-3xl bg-gradient-to-r from-primary-container/20 via-transparent to-secondary-container/20 blur-3xl sm:h-40" />
      </div>
    </div>
  );
}

function MetricCard(props: {
  label: string;
  badge: string;
  badgeVariant: "primary" | "error" | "neutral";
  value: string;
  sub: string;
  spark: string;
  path: string;
}) {
  const badge =
    props.badgeVariant === "primary"
      ? "bg-primary/10 text-primary"
      : props.badgeVariant === "error"
        ? "bg-error/10 text-error"
        : "bg-outline/10 text-outline";
  return (
    <motion.div
      variants={cardVariants}
      whileHover={{ y: -2, transition: { duration: 0.15 } }}
      className="ghost-border flex min-h-0 min-w-0 flex-col gap-3 overflow-hidden rounded-xl bg-surface-container-low p-4 sm:gap-4 sm:p-6 cursor-default"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wider text-secondary">
          {props.label}
        </span>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-bold ${badge}`}>
          {props.badge}
        </span>
      </div>
      <div className="min-w-0">
        <h3 className="truncate text-2xl font-extrabold tracking-tighter text-on-surface sm:text-3xl">
          {props.value}
        </h3>
        <p className="mt-1 line-clamp-2 text-xs text-outline">{props.sub}</p>
      </div>
      <div className="mt-1 h-10 w-full min-w-0 shrink-0">
        <svg className="h-full w-full" viewBox="0 0 100 20" preserveAspectRatio="none">
          <path d={props.path} fill="none" stroke={props.spark} strokeWidth="2" />
        </svg>
      </div>
    </motion.div>
  );
}

function BarRow(props: {
  name: string;
  val: string;
  width: number;
  tone: "100" | "80" | "60" | "40";
}) {
  const bg =
    props.tone === "100"
      ? "bg-primary"
      : props.tone === "80"
        ? "bg-primary/80"
        : props.tone === "60"
          ? "bg-primary/60"
          : "bg-primary/40";
  return (
    <div className="min-w-0 space-y-2">
      <div className="flex justify-between gap-2 text-xs">
        <span className="min-w-0 truncate font-medium text-on-surface">{props.name}</span>
        <span className="shrink-0 text-secondary">{props.val}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-container-highest">
        <motion.div
          className={`h-full max-w-full rounded-full ${bg}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(4, props.width))}%` }}
          transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1], delay: 0.1 }}
        />
      </div>
    </div>
  );
}

function InsightRow(props: {
  icon: string;
  iconClass: string;
  text: string;
  fill?: boolean;
}) {
  return (
    <div className="flex min-w-0 gap-3">
      <div className="mt-0.5 shrink-0">
        <span
          className={`material-symbols-outlined text-sm ${props.iconClass}`}
          style={props.fill ? { fontVariationSettings: "'FILL' 1" } : undefined}
        >
          {props.icon}
        </span>
      </div>
      <p className="min-w-0 break-words text-[11px] leading-relaxed text-secondary">
        {props.text}
      </p>
    </div>
  );
}
