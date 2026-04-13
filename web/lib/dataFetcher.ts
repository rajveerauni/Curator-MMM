/**
 * Real external data via public Yahoo Finance JSON endpoints (no API key) and
 * news (NewsAPI when configured, otherwise Google News RSS).
 */

import Parser from "rss-parser";
import type { NewsArticle, StockPayload, StockSeriesPoint } from "@/lib/types";

const RSS_PARSER = new Parser({
  timeout: 12_000,
  headers: {
    "User-Agent": "CuratorMMM/1.0 (research; +https://example.local)",
  },
});

const YAHOO_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";

async function yahooFetch(url: string): Promise<Response> {
  return fetch(url, {
    cache: "no-store",
    headers: {
      "User-Agent": YAHOO_UA,
      Accept: "application/json,text/plain,*/*",
    },
  });
}

export type TickerResolution = { symbol: string; name: string };

type YahooSearchQuote = {
  symbol?: string;
  shortname?: string;
  longname?: string;
  quoteType?: string;
};

/**
 * Resolve a free-text company query to an equity symbol using Yahoo search.
 */
export async function resolveCompanyToTicker(query: string): Promise<TickerResolution | null> {
  const trimmed = query.trim();
  if (!trimmed) return null;

  const url = `https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(trimmed)}`;
  const res = await yahooFetch(url);
  if (!res.ok) {
    throw new Error(`Yahoo search failed (${res.status})`);
  }
  const data = (await res.json()) as { quotes?: YahooSearchQuote[] };
  const quotes = data.quotes ?? [];
  const equity = quotes.find(
    (q) => q.quoteType === "EQUITY" && typeof q.symbol === "string" && q.symbol.length > 0
  );
  if (!equity?.symbol) return null;

  const name = equity.shortname || equity.longname || equity.symbol;
  return { symbol: equity.symbol.toUpperCase(), name: String(name) };
}

function trendFromCloses(closes: number[]): StockPayload["trendLabel"] {
  if (closes.length < 5) return "unknown";
  const recent = closes.slice(-5);
  const older = closes.slice(-15, -5);
  if (older.length === 0) return "unknown";
  const mR = recent.reduce((a, b) => a + b, 0) / recent.length;
  const mO = older.reduce((a, b) => a + b, 0) / older.length;
  const delta = (mR - mO) / (mO || 1);
  if (delta > 0.02) return "up";
  if (delta < -0.02) return "down";
  return "flat";
}

type ChartMeta = {
  currency?: string;
  symbol?: string;
  shortName?: string;
  longName?: string;
  regularMarketPrice?: number;
  chartPreviousClose?: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
  regularMarketVolume?: number;
};

/**
 * Fetch ~3 months of daily OHLCV plus live meta from Yahoo **chart** API.
 * (The v7 ``quote`` endpoint often returns 401 for server-side clients.)
 */
export async function fetchStockData(ticker: string): Promise<StockPayload> {
  const upper = ticker.trim().toUpperCase();

  const chartUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(
    upper
  )}?interval=1d&range=3mo`;
  const chartRes = await yahooFetch(chartUrl);
  if (!chartRes.ok) {
    throw new Error(`Yahoo chart failed (${chartRes.status})`);
  }
  const chartJson = (await chartRes.json()) as {
    chart?: {
      error?: unknown;
      result?: Array<{
        meta?: ChartMeta;
        timestamp?: number[];
        indicators?: {
          quote?: Array<{
            close?: Array<number | null>;
            volume?: Array<number | null>;
          }>;
        };
      }>;
    };
  };

  const result = chartJson.chart?.result?.[0];
  if (!result) {
    throw new Error(`No chart data for ${upper}`);
  }

  const meta = result.meta ?? {};
  const ts = result.timestamp ?? [];
  const qRow = result.indicators?.quote?.[0];
  const closes = qRow?.close ?? [];
  const volumes = qRow?.volume ?? [];

  const series: StockSeriesPoint[] = ts
    .map((t, i) => {
      const c = closes[i];
      if (typeof c !== "number" || Number.isNaN(c)) return null;
      return {
        date: new Date(t * 1000).toISOString().slice(0, 10),
        close: c,
      };
    })
    .filter((x): x is StockSeriesPoint => x !== null);

  const closeVals = series.map((p) => p.close);
  const trendLabel = trendFromCloses(closeVals);

  const price =
    typeof meta.regularMarketPrice === "number" ? meta.regularMarketPrice : null;
  const prevClose =
    typeof meta.chartPreviousClose === "number" ? meta.chartPreviousClose : null;
  const change =
    price != null && prevClose != null ? price - prevClose : null;
  const changePct =
    price != null && prevClose != null && prevClose !== 0
      ? ((price - prevClose) / prevClose) * 100
      : null;

  const volSample = volumes
    .filter((v): v is number => typeof v === "number" && !Number.isNaN(v))
    .slice(-60);
  const avgVol =
    volSample.length > 0
      ? volSample.reduce((a, b) => a + b, 0) / volSample.length
      : typeof meta.regularMarketVolume === "number"
        ? meta.regularMarketVolume
        : null;

  return {
    ticker: upper,
    name: meta.shortName || meta.longName || upper,
    currency: meta.currency || "USD",
    regularMarketPrice: price,
    regularMarketChange: change,
    regularMarketChangePercent: changePct,
    marketCap: null,
    fiftyTwoWeekHigh:
      typeof meta.fiftyTwoWeekHigh === "number" ? meta.fiftyTwoWeekHigh : null,
    fiftyTwoWeekLow:
      typeof meta.fiftyTwoWeekLow === "number" ? meta.fiftyTwoWeekLow : null,
    averageVolume: avgVol,
    trendLabel,
    series,
  };
}

type NewsApiResponse = {
  status: string;
  articles?: Array<{
    title: string | null;
    url: string;
    publishedAt: string | null;
    source?: { name?: string | null };
  }>;
};

/**
 * Headlines for a company: NewsAPI when `NEWS_API_KEY` is set, otherwise Google News RSS.
 */
export async function fetchCompanyNews(
  company: string,
  newsApiKey: string | null
): Promise<{ articles: NewsArticle[]; source: "newsapi" | "google_rss" }> {
  const q = company.trim();
  if (!q) return { articles: [], source: "google_rss" };

  if (newsApiKey) {
    const url = new URL("https://newsapi.org/v2/everything");
    url.searchParams.set("q", q);
    url.searchParams.set("language", "en");
    url.searchParams.set("sortBy", "publishedAt");
    url.searchParams.set("pageSize", "12");
    url.searchParams.set("apiKey", newsApiKey);

    const res = await fetch(url.toString(), { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`NewsAPI error ${res.status}`);
    }
    const data = (await res.json()) as NewsApiResponse;
    if (data.status !== "ok" || !data.articles) {
      throw new Error("NewsAPI returned no articles");
    }
    const articles: NewsArticle[] = data.articles
      .filter((a) => a.title && a.url)
      .map((a) => ({
        title: a.title as string,
        link: a.url,
        publishedAt: a.publishedAt,
        source: a.source?.name ?? null,
      }));
    return { articles, source: "newsapi" };
  }

  const rssUrl = `https://news.google.com/rss/search?q=${encodeURIComponent(q)}&hl=en-US&gl=US&ceid=US:en`;
  const feed = await RSS_PARSER.parseURL(rssUrl);
  const items = feed.items ?? [];
  const articles: NewsArticle[] = items.slice(0, 12).map((it) => ({
    title: it.title ?? "Untitled",
    link: it.link ?? "#",
    publishedAt: it.pubDate ?? null,
    source: it.source?.name ?? "Google News",
  }));

  return { articles, source: "google_rss" };
}
