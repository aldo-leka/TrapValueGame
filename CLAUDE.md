# Trap Or Value: Project Memory

## Tech Stack
- **Framework:** .NET 10 Blazor (Interactive Server) + MudBlazor
- **Data Engine:** Python 3.12+ (yfinance, FastAPI)
- **Database:** SQLite (Shared Volume: `/shared/stocks.db`)
- **AI Integration:** Gemini 1.5 Flash/Pro via Microsoft.Extensions.AI

## Core Concept: The "Snapshot"
The game presents a stock at a specific **Historical Date (T-0)**.
- **The Data:** 5 years of financial history *prior* to T-0.
- **The Narrative:** AI summarizes the news/sentiment *at* T-0.
  Example system prompt: "You are a value investing mentor in 2015. Describe this company's current struggles based on the provided data, highlighting the 'bear case' and 'bull case' without revealing the company name."
- **The Outcome:** The actual stock performance 24 months *after* T-0.

## Critical Rules
- **Point-in-Time Integrity:** NEVER show data or news dated after the SnapshotDate during the "Guess" phase.
- **Split Accuracy:** ALWAYS use `auto_adjust=True` in yfinance to prevent fake "price drops" from splits.
- **Formatting:** Negative financials = Red + Brackets: `(125.50)`.
- **Project Structure:** - `/app`: Blazor UI (MudBlazor)
    - `/scripts`: Python API & Scraper
    - `/shared`: SQLite DB & Static assets