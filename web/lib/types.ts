/**
 * Shared types for the company intelligence API and UI.
 */

export type StockSeriesPoint = { date: string; close: number };

export type StockPayload = {
  ticker: string;
  name: string;
  currency: string;
  regularMarketPrice: number | null;
  regularMarketChange: number | null;
  regularMarketChangePercent: number | null;
  marketCap: number | null;
  fiftyTwoWeekHigh: number | null;
  fiftyTwoWeekLow: number | null;
  averageVolume: number | null;
  /** Simple trend label derived from recent closes (not predictive). */
  trendLabel: "up" | "down" | "flat" | "unknown";
  series: StockSeriesPoint[];
};

export type NewsArticle = {
  title: string;
  link: string;
  publishedAt: string | null;
  source: string | null;
};

export type AiInsightBlock = {
  keyInsights: string[];
  channelAssumptions: string[];
  strategicRecommendations: string[];
  riskNotes: string[];
};

export type CompanyIntelligenceResponse = {
  query: string;
  ticker: string;
  resolvedName: string;
  stock: StockPayload;
  news: NewsArticle[];
  newsSource: "newsapi" | "google_rss";
  insights: AiInsightBlock | null;
  insightsError: string | null;
  warnings: string[];
};
