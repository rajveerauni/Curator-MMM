# Curator — AI marketing intelligence (Next.js)

Real-data pipeline:

1. **Yahoo Finance** (no API key): search + chart JSON for price, change %, 52w range, volume, daily closes.
2. **News**: **NewsAPI.org** when `NEWS_API_KEY` is set; otherwise **Google News RSS** (no key).
3. **Groq**: server-side insights via `groq-sdk` when `GROQ_API_KEY` is set.

## Setup

```bash
cd web
cp .env.local.example .env.local
# Edit .env.local — add GROQ_API_KEY (required for AI). NEWS_API_KEY is optional.
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) (or the port Next prints).

## API

`GET /api/company?company=Tesla` returns JSON with `stock`, `news`, `insights` (or `insightsError` if Groq is missing/failed).

Secrets stay on the server; the browser only calls your Next route.

## Production notes

- Yahoo may rate-limit or change JSON shapes; handle 502s in the UI (already surfaced).
- Chart endpoint omits **market cap**; we show `null` / “not in feed” instead of fabricating values.
