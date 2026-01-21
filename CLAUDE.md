# Trap Or Value: Project Memory

## Overview
A financial guessing game where players analyze historical stock data presented at a "snapshot" moment in time, then decide if the stock was a **Value** opportunity or a **Trap**. The reveal shows what actually happened over the next 24 months.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | .NET 10 Blazor (Interactive Server) | Real-time UI, swipe interactions |
| **UI Components** | MudBlazor | Dark mode, data tables, charts |
| **Data API** | Python 3.12+ / FastAPI | Stock data fetching, preprocessing |
| **Data Source** | yfinance | Historical prices & financials |
| **Database** | SQLite | Snapshot storage, game state |
| **AI Narratives** | Gemini 3 Flash/Pro | Period-accurate story generation |
| **AI SDK** | Microsoft.Extensions.AI | .NET ↔ Gemini integration |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BLAZOR SERVER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ GamePage.razor│  │ TableComponent│  │ SwipeComponent      │ │
│  │              │  │ (TIKR-style) │  │ (Touch + Mouse)      │ │
│  └──────┬───────┘  └──────────────┘  └───────────────────────┘ │
│         │                                                       │
│  ┌──────▼───────────────────────────────────────────────────┐  │
│  │               GameService.cs                              │  │
│  │  - GetNextSnapshot() → calls Python API                   │  │
│  │  - RevealOutcome() → fetches result + real ticker         │  │
│  │  - GenerateNarrative() → calls Gemini                     │  │
│  └──────┬───────────────────────────────────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │ HTTP
┌─────────▼───────────────────────────────────────────────────────┐
│                      PYTHON FASTAPI                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ /game/next   │  │ /game/reveal │  │ /admin/seed           │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────────┘ │
│         │                 │                                     │
│  ┌──────▼─────────────────▼─────────────────────────────────┐  │
│  │               DataService (yfinance)                      │  │
│  │  - fetch_financials(ticker, before_date)                  │  │
│  │  - calculate_forward_return(ticker, date, months=24)      │  │
│  │  - validate_data_quality(ticker)                          │  │
│  └──────┬───────────────────────────────────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────┐
│                      SHARED VOLUME                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /shared/stocks.db (SQLite)                               │  │
│  │  - stocks, financials, snapshots, game_sessions           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concept: The "Snapshot"

The game presents a stock at a specific **Historical Date (T-0)**.

| Phase | What Player Sees | Data Source |
|-------|------------------|-------------|
| **Analysis** | 5 years of financials ending at T-0 | SQLite (pre-computed) |
| **Narrative** | AI-generated "state of the company" at T-0 | Gemini (with context) |
| **Guess** | Swipe LEFT (Trap) or RIGHT (Value) | User input |
| **Reveal** | Actual price chart T-0 → T+24mo, real name | SQLite + yfinance |

---

## Critical Rules

### 1. Point-in-Time Integrity
**NEVER** show data or news dated after the `SnapshotDate` during the "Guess" phase.
- Financials: `WHERE report_date <= snapshot_date`
- AI Prompt: "You are analyzing this company in [YEAR]. Do not reference any events after [DATE]."

### 2. Split Accuracy
**ALWAYS** use `auto_adjust=True` in yfinance to prevent fake "price drops" from stock splits.
```python
ticker.history(start=date, end=end_date, auto_adjust=True)
```

### 3. Formatting Standards
- Negative financials = Red text + Brackets: `(125.50)`
- Large numbers: Always show in millions with 1 decimal: `$1,234.5M`
- Percentages: 1 decimal place: `23.4%`
- Dates: `MMM YYYY` for display: `Jan 2018`

### 4. Project Structure
```
/TrapValueGame
├── /app                    # Blazor Server Application
│   ├── /Components         # Razor components
│   ├── /Services           # GameService, GeminiService
│   ├── /Models             # DTOs, ViewModels
│   └── Program.cs
├── /scripts                # Python Data Engine
│   ├── /api                # FastAPI endpoints
│   ├── /services           # yfinance wrapper, data processing
│   ├── /models             # Pydantic schemas
│   └── main.py
├── /shared                 # Shared Volume
│   ├── stocks.db           # SQLite database
│   └── /cache              # yfinance response cache
├── /.claude                # Project documentation
│   ├── data-pipeline.md
│   ├── ui-ux.md
│   ├── implementation-roadmap.md
│   └── stock-selection.md
├── docker-compose.yml
└── CLAUDE.md               # This file
```

---

## Environment Variables

```env
# Blazor App
PYTHON_API_URL=http://localhost:8000
GEMINI_API_KEY=your-key-here
DATABASE_PATH=/shared/stocks.db

# Python API
DATABASE_PATH=/shared/stocks.db
YFINANCE_CACHE_DIR=/shared/cache
```

---

## Quick Reference: Key Files to Modify

| Task | Primary File(s) |
|------|-----------------|
| Add new financial metric | `data-pipeline.md` → `Financials` schema |
| Change swipe behavior | `ui-ux.md` → Swipe Component |
| Add new stock criteria | `stock-selection.md` |
| Modify game flow | `implementation-roadmap.md` Phase 3 |