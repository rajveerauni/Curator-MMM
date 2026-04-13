/**
 * Groq-powered marketing insights (server-side only).
 */

import Groq from "groq-sdk";
import type { AiInsightBlock, NewsArticle, StockPayload } from "@/lib/types";

const MODEL = "llama-3.3-70b-versatile";

function stripJsonFence(text: string): string {
  const t = text.trim();
  if (t.startsWith("```")) {
    return t.replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/i, "").trim();
  }
  return t;
}

export function isGroqConfigured(): boolean {
  return Boolean(process.env.GROQ_API_KEY?.trim());
}

/**
 * Sends structured market + news context to Groq and returns parsed insight sections.
 */
export async function generateMarketingInsights(input: {
  companyQuery: string;
  ticker: string;
  resolvedName: string;
  stock: StockPayload;
  news: NewsArticle[];
}): Promise<AiInsightBlock> {
  const key = process.env.GROQ_API_KEY?.trim();
  if (!key) {
    throw new Error("GROQ_API_KEY is not set");
  }

  const groq = new Groq({ apiKey: key });

  const newsBullets = input.news
    .slice(0, 10)
    .map((n) => `- ${n.title} (${n.source ?? "source unknown"})`)
    .join("\n");

  const lastCloses = input.stock.series.slice(-10).map((p) => `${p.date}:${p.close}`);
  const stockBlock = [
    `Ticker: ${input.stock.ticker}`,
    `Name: ${input.resolvedName}`,
    `Price: ${input.stock.regularMarketPrice ?? "n/a"} ${input.stock.currency}`,
    `Change%: ${input.stock.regularMarketChangePercent ?? "n/a"}`,
    `Market cap: ${input.stock.marketCap ?? "n/a"}`,
    `52w high/low: ${input.stock.fiftyTwoWeekHigh ?? "n/a"} / ${input.stock.fiftyTwoWeekLow ?? "n/a"}`,
    `Volume (avg 3m): ${input.stock.averageVolume ?? "n/a"}`,
    `Heuristic trend (90d daily): ${input.stock.trendLabel}`,
    `Recent closes: ${lastCloses.join(", ")}`,
  ].join("\n");

  const userContent = `You are a senior marketing analyst. Use ONLY the data below. Do not invent financial numbers. If data is missing, say so in riskNotes.

Company query: ${input.companyQuery}
Resolved equity: ${input.ticker} — ${input.resolvedName}

=== Market data (Yahoo Finance) ===
${stockBlock}

=== Recent headlines ===
${newsBullets || "(no headlines returned)"}

Return ONLY valid JSON (no markdown) with this exact shape:
{
  "keyInsights": string[],
  "channelAssumptions": string[],
  "strategicRecommendations": string[],
  "riskNotes": string[]
}

Rules:
- keyInsights: 3–5 bullets tying brand momentum, pricing power, and narrative risk to marketing.
- channelAssumptions: plausible channel hypotheses (e.g. search, social, retail, events) explicitly labeled as assumptions, not facts.
- strategicRecommendations: 3–5 actionable marketing moves grounded in the headlines/trend.
- riskNotes: compliance + data limitations (you are not verifying claims in articles).`;

  const completion = await groq.chat.completions.create({
    model: MODEL,
    temperature: 0.35,
    max_tokens: 1200,
    messages: [
      {
        role: "system",
        content:
          "You output JSON only. Never include markdown fences. Arrays must contain non-empty strings.",
      },
      { role: "user", content: userContent },
    ],
  });

  const raw = completion.choices[0]?.message?.content?.trim();
  if (!raw) {
    throw new Error("Empty Groq response");
  }

  const parsed = JSON.parse(stripJsonFence(raw)) as Partial<AiInsightBlock>;
  const normalize = (v: unknown): string[] =>
    Array.isArray(v) ? v.filter((x) => typeof x === "string" && x.trim()) : [];

  const block: AiInsightBlock = {
    keyInsights: normalize(parsed.keyInsights),
    channelAssumptions: normalize(parsed.channelAssumptions),
    strategicRecommendations: normalize(parsed.strategicRecommendations),
    riskNotes: normalize(parsed.riskNotes),
  };

  if (
    block.keyInsights.length === 0 &&
    block.strategicRecommendations.length === 0
  ) {
    throw new Error("Groq returned empty insight arrays");
  }

  return block;
}
