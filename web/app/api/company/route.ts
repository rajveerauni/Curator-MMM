import { NextResponse } from "next/server";

import { generateMarketingInsights, isGroqConfigured } from "@/lib/ai";
import {
  fetchCompanyNews,
  fetchStockData,
  resolveCompanyToTicker,
} from "@/lib/dataFetcher";
import type { CompanyIntelligenceResponse } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/company?company=Tesla
 * Pipeline: resolve ticker → Yahoo Finance → news (NewsAPI or RSS) → Groq insights.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const company = searchParams.get("company")?.trim() ?? "";

  if (!company) {
    return NextResponse.json(
      { error: "Missing required query parameter: company" },
      { status: 400 }
    );
  }

  const warnings: string[] = [];

  let resolved;
  try {
    resolved = await resolveCompanyToTicker(company);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Ticker lookup failed";
    return NextResponse.json({ error: msg }, { status: 502 });
  }

  if (!resolved) {
    return NextResponse.json(
      { error: `No equity match found for "${company}". Try a different spelling or add a ticker (e.g. TSLA).` },
      { status: 404 }
    );
  }

  let stock;
  try {
    stock = await fetchStockData(resolved.symbol);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Stock fetch failed";
    return NextResponse.json({ error: msg }, { status: 502 });
  }

  const newsKey = process.env.NEWS_API_KEY?.trim() || null;
  let newsPack: Awaited<ReturnType<typeof fetchCompanyNews>>;
  try {
    newsPack = await fetchCompanyNews(resolved.name || company, newsKey);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "News fetch failed";
    warnings.push(`News unavailable: ${msg}. Retry later or set NEWS_API_KEY.`);
    newsPack = { articles: [], source: "google_rss" };
  }

  if (!newsKey) {
    warnings.push("Using Google News RSS (no NEWS_API_KEY). Add NEWS_API_KEY for NewsAPI.org.");
  }

  let insights = null as Awaited<ReturnType<typeof generateMarketingInsights>> | null;
  let insightsError: string | null = null;

  if (!isGroqConfigured()) {
    insightsError =
      "GROQ_API_KEY is not configured. Add it to web/.env.local to enable AI insights.";
  } else {
    try {
      insights = await generateMarketingInsights({
        companyQuery: company,
        ticker: resolved.symbol,
        resolvedName: resolved.name,
        stock,
        news: newsPack.articles,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Groq request failed";
      insightsError = msg;
    }
  }

  const body: CompanyIntelligenceResponse = {
    query: company,
    ticker: resolved.symbol,
    resolvedName: resolved.name,
    stock,
    news: newsPack.articles,
    newsSource: newsPack.source,
    insights,
    insightsError,
    warnings,
  };

  return NextResponse.json(body);
}
