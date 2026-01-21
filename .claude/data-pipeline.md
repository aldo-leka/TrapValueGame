# Data Rules: Scraper & SQLite

## Database Schema (SQLite)
- **Stocks:** `Id, FakeName, RealTicker, Sector, Industry`
- **Financials:** `StockId, ReportDate, Revenue, EBITDA, FCF, TotalDebt, Cash, Shares`
- **Snapshots:** `StockId, SnapshotDate, PriceAtDate, PriceTwoYearsLater, NarrativeSummary`

## Python Logic (The "Time Machine")
- **Scraper:** For a given Ticker and SnapshotDate:
    1. Fetch `info` and `history`.
    2. Extract financials where `Date < SnapshotDate`.
    3. Calculate 2-year Forward ROI: `(Price(T+730) / Price(T)) - 1`.
- **Narrative Generator (Gemini):** - Prompt: "Search for news/filings for [Ticker] around [Date]. Summarize the prevailing market sentiment and 3 key risks mentioned in 10-K filings *at that time*. Do not mention the company name."

## API Endpoints
- `GET /game/next`: Returns a random Snapshot + Financials (obfuscated).
- `POST /game/reveal/{id}`: Returns the Ticker, Real Name, and Price Action.