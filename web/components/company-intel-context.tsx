"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useDebouncedValue } from "@/components/use-debounced-value";
import { downloadJsonFile } from "@/lib/download-json";
import type { CompanyIntelligenceResponse } from "@/lib/types";

type CompanyIntelContextValue = {
  query: string;
  setQuery: (q: string) => void;
  debouncedQuery: string;
  data: CompanyIntelligenceResponse | null;
  loading: boolean;
  error: string | null;
  exportReport: () => void;
  exportMessage: string | null;
  clearExportMessage: () => void;
};

const CompanyIntelContext = createContext<CompanyIntelContextValue | null>(null);

export function CompanyIntelProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query.trim(), 450);
  const [data, setData] = useState<CompanyIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  const runFetch = useCallback(async (company: string) => {
    if (!company) {
      setData(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/company?company=${encodeURIComponent(company)}`, {
        cache: "no-store",
      });
      const json = (await res.json()) as CompanyIntelligenceResponse & { error?: string };
      if (!res.ok) {
        setData(null);
        setError(json.error || `Request failed (${res.status})`);
        return;
      }
      setData(json as CompanyIntelligenceResponse);
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void runFetch(debouncedQuery);
  }, [debouncedQuery, runFetch]);

  const exportReport = useCallback(() => {
    setExportMessage(null);
    if (!data) {
      setExportMessage("Search for a company first, then export.");
      return;
    }
    const safeName = data.ticker.replace(/[^a-zA-Z0-9-_]/g, "_") || "company";
    const payload = {
      exportedAt: new Date().toISOString(),
      query: data.query,
      resolvedName: data.resolvedName,
      ticker: data.ticker,
      stock: data.stock,
      newsSource: data.newsSource,
      news: data.news.map((n) => ({
        title: n.title,
        link: n.link,
        publishedAt: n.publishedAt,
        source: n.source,
      })),
      insights: data.insights,
      insightsError: data.insightsError,
      warnings: data.warnings,
    };
    downloadJsonFile(`curator-report-${safeName}-${Date.now()}.json`, payload);
  }, [data]);

  const clearExportMessage = useCallback(() => setExportMessage(null), []);

  const value = useMemo(
    () => ({
      query,
      setQuery,
      debouncedQuery,
      data,
      loading,
      error,
      exportReport,
      exportMessage,
      clearExportMessage,
    }),
    [
      query,
      debouncedQuery,
      data,
      loading,
      error,
      exportReport,
      exportMessage,
      clearExportMessage,
    ]
  );

  return (
    <CompanyIntelContext.Provider value={value}>{children}</CompanyIntelContext.Provider>
  );
}

export function useCompanyIntel(): CompanyIntelContextValue {
  const ctx = useContext(CompanyIntelContext);
  if (!ctx) {
    throw new Error("useCompanyIntel must be used within CompanyIntelProvider");
  }
  return ctx;
}
