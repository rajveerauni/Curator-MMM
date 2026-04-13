import type { CompanyIntelligenceResponse, StockSeriesPoint } from "@/lib/types";

/** Scale closes into viewBox 0..1000 x 0..300 (y inverted). */
export function buildPriceChartPaths(series: StockSeriesPoint[]): {
  lineD: string;
  areaD: string;
  secondaryD: string;
  startDate: string;
  midDate: string;
  endDate: string;
} {
  if (series.length < 2) {
    return {
      lineD: "",
      areaD: "",
      secondaryD: "",
      startDate: "—",
      midDate: "—",
      endDate: "—",
    };
  }

  const closes = series.map((p) => p.close);
  const sma = simpleMovingAverage(closes, 5);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const pad = (max - min) * 0.08 || 1;
  const lo = min - pad;
  const hi = max + pad;

  const n = series.length;
  const xAt = (i: number) => (i / (n - 1)) * 1000;

  const yAt = (price: number) => {
    const t = (price - lo) / (hi - lo);
    return 280 - t * 260;
  };

  const linePts = series.map((p, i) => ({
    x: xAt(i),
    y: yAt(p.close),
  }));

  const lineD = linePts
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  const areaD = `${lineD} L 1000 300 L 0 300 Z`;

  const secondaryD = sma
    .map((v, i) => {
      if (v == null || Number.isNaN(v)) return null;
      return { x: xAt(i), y: yAt(v) };
    })
    .filter((p): p is { x: number; y: number } => p !== null)
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  const startDate = series[0].date;
  const endDate = series[n - 1].date;
  const midDate = series[Math.floor(n / 2)].date;

  return { lineD, areaD, secondaryD, startDate, midDate, endDate };
}

function simpleMovingAverage(values: number[], window: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < window) return null;
    const slice = values.slice(i + 1 - window, i + 1);
    return slice.reduce((a, b) => a + b, 0) / window;
  });
}

export function rangePositionPct(stock: CompanyIntelligenceResponse["stock"]): number {
  const { regularMarketPrice: p, fiftyTwoWeekHigh: h, fiftyTwoWeekLow: l } = stock;
  if (p == null || h == null || l == null || h <= l) return 0;
  const t = (p - l) / (h - l);
  return Math.round(Math.min(1, Math.max(0, t)) * 100);
}

export function drawdownFromHighPct(stock: CompanyIntelligenceResponse["stock"]): number | null {
  const { regularMarketPrice: p, fiftyTwoWeekHigh: h } = stock;
  if (p == null || h == null || h === 0) return null;
  return ((h - p) / h) * 100;
}

export function trendBarWidth(trend: CompanyIntelligenceResponse["stock"]["trendLabel"]): number {
  switch (trend) {
    case "up":
      return 82;
    case "down":
      return 38;
    case "flat":
      return 55;
    default:
      return 45;
  }
}

export function volatilityBarWidth(series: StockSeriesPoint[]): number {
  if (series.length < 6) return 30;
  const rets: number[] = [];
  for (let i = 1; i < series.length; i++) {
    const a = series[i - 1].close;
    const b = series[i].close;
    if (a === 0) continue;
    rets.push((b - a) / a);
  }
  if (rets.length === 0) return 30;
  const mean = rets.reduce((x, y) => x + y, 0) / rets.length;
  const var_ =
    rets.reduce((s, r) => s + (r - mean) ** 2, 0) / Math.max(1, rets.length - 1);
  const vol = Math.sqrt(var_);
  const pct = Math.min(100, Math.round(vol * 800));
  return Math.max(18, pct);
}

export function donutSegments(data: CompanyIntelligenceResponse | null): {
  a: number;
  b: number;
  c: number;
  label: string;
} {
  if (!data) return { a: 45, b: 30, c: 25, label: "Search" };
  const rp = rangePositionPct(data.stock);
  const news = Math.min(100, Math.round((data.news.length / 12) * 100));
  const ai = data.insights ? 70 : 15;
  const sum = rp + news + ai || 1;
  const a = Math.round((rp / sum) * 100);
  const b = Math.round((news / sum) * 100);
  const c = Math.max(0, 100 - a - b);
  return { a, b, c, label: `${rp}% range` };
}
