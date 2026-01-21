# Implementation Roadmap: Phase-by-Phase Development

This document outlines the step-by-step implementation plan for building Trap Or Value from scratch.

---

## Overview

| Phase | Focus | Deliverable |
|-------|-------|-------------|
| **Phase 1** | Project Setup & Infrastructure | Docker environment, project scaffolding |
| **Phase 2** | Data Pipeline | Python scraper, SQLite schema, seed data |
| **Phase 3** | Core Game API | FastAPI endpoints, data service |
| **Phase 4** | Blazor Foundation | Basic UI, MudBlazor setup, routing |
| **Phase 5** | Game UI Components | Financial table, swipe card, result view |
| **Phase 6** | AI Narrative Integration | Gemini integration, prompt engineering |
| **Phase 7** | Polish & Testing | Animations, edge cases, performance |
| **Phase 8** | Deployment | Production setup, monitoring |

---

## Phase 1: Project Setup & Infrastructure

### Goals
- Set up development environment
- Create project structure
- Configure Docker for local development

### Tasks

#### 1.1 Initialize Repository Structure
```bash
mkdir -p app/Components app/Services app/Models
mkdir -p scripts/api scripts/services scripts/models
mkdir -p shared/cache
touch docker-compose.yml
touch app/Program.cs
touch scripts/main.py
touch scripts/requirements.txt
```

#### 1.2 Create Blazor Server Project
```bash
cd app
dotnet new blazorserver -n TrapValueGame -f net10.0
dotnet add package MudBlazor
dotnet add package Microsoft.Extensions.AI
dotnet add package Microsoft.Extensions.AI.OpenAI  # For Gemini compatibility
dotnet add package Microsoft.Data.Sqlite
```

**app/Program.cs** - Initial setup:
```csharp
using MudBlazor.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddMudServices();

// Add custom services
builder.Services.AddHttpClient("PythonApi", client => {
    client.BaseAddress = new Uri(
        builder.Configuration["PythonApiUrl"] ?? "http://localhost:8000"
    );
});

builder.Services.AddScoped<GameService>();
builder.Services.AddScoped<GameStateService>();

var app = builder.Build();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
```

#### 1.3 Create Python FastAPI Project
**scripts/requirements.txt:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
yfinance==0.2.36
pandas==2.2.0
pydantic==2.6.0
aiosqlite==0.19.0
python-dotenv==1.0.0
httpx==0.26.0
```

**scripts/main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import game_router, admin_router
from services.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Trap Or Value API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router, prefix="/game", tags=["Game"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

#### 1.4 Docker Compose Configuration
**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    ports:
      - "5000:8080"
    environment:
      - ASPNETCORE_ENVIRONMENT=Development
      - PythonApiUrl=http://api:8000
      - DatabasePath=/shared/stocks.db
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./shared:/shared
    depends_on:
      - api

  api:
    build:
      context: ./scripts
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_PATH=/shared/stocks.db
      - CACHE_DIR=/shared/cache
    volumes:
      - ./shared:/shared

volumes:
  shared:
```

**app/Dockerfile:**
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY . .
RUN dotnet restore
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENTRYPOINT ["dotnet", "TrapValueGame.dll"]
```

**scripts/Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Verification
- [ ] `docker-compose up` starts both services
- [ ] Blazor app accessible at http://localhost:5000
- [ ] Python API health check at http://localhost:8000/health

---

## Phase 2: Data Pipeline

### Goals
- Create SQLite database schema
- Build yfinance data extraction
- Implement snapshot generation logic

### Tasks

#### 2.1 Database Schema
**scripts/services/database.py:**
```python
import aiosqlite
from pathlib import Path
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/shared/stocks.db")

async def init_db():
    """Initialize database with schema."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                company_name TEXT NOT NULL,
                fake_name TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                market_cap_tier TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS financials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL REFERENCES stocks(id),
                fiscal_year INTEGER NOT NULL,
                report_date DATE NOT NULL,
                revenue REAL,
                gross_profit REAL,
                operating_income REAL,
                ebitda REAL,
                net_income REAL,
                gross_margin REAL,
                operating_margin REAL,
                net_margin REAL,
                total_assets REAL,
                total_debt REAL,
                cash_and_equivalents REAL,
                total_equity REAL,
                operating_cash_flow REAL,
                capital_expenditures REAL,
                free_cash_flow REAL,
                shares_outstanding REAL,
                UNIQUE(stock_id, fiscal_year)
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL REFERENCES stocks(id),
                date DATE NOT NULL,
                adj_close REAL NOT NULL,
                volume INTEGER,
                UNIQUE(stock_id, date)
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL REFERENCES stocks(id),
                snapshot_date DATE NOT NULL,
                price_at_snapshot REAL NOT NULL,
                price_at_6mo REAL,
                price_at_12mo REAL,
                price_at_24mo REAL NOT NULL,
                return_6mo REAL,
                return_12mo REAL,
                return_24mo REAL NOT NULL,
                narrative TEXT,
                narrative_generated_at DATETIME,
                outcome_label TEXT,
                difficulty TEXT,
                times_played INTEGER DEFAULT 0,
                correct_guesses INTEGER DEFAULT 0,
                UNIQUE(stock_id, snapshot_date)
            );

            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
                player_choice TEXT NOT NULL,
                is_correct BOOLEAN,
                played_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_snapshots_outcome ON snapshots(outcome_label);
            CREATE INDEX IF NOT EXISTS idx_snapshots_difficulty ON snapshots(difficulty);
            CREATE INDEX IF NOT EXISTS idx_financials_stock ON financials(stock_id);
            CREATE INDEX IF NOT EXISTS idx_prices_stock_date ON price_history(stock_id, date);
        """)
        await db.commit()

async def get_db():
    """Get database connection."""
    return await aiosqlite.connect(DATABASE_PATH)
```

#### 2.2 yfinance Extractor Service
**scripts/services/extractor.py:**
```python
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

class YFinanceExtractor:
    """Extract and normalize stock data from yfinance."""

    MILLION = 1_000_000

    def fetch_company_info(self, symbol: str) -> dict:
        """Get company metadata."""
        ticker = yf.Ticker(symbol)
        info = ticker.info

        return {
            "ticker": symbol.upper(),
            "company_name": info.get("longName") or info.get("shortName", "Unknown"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap_tier": self._classify_market_cap(info.get("marketCap", 0))
        }

    def fetch_financials(self, symbol: str, before_date: datetime) -> list[dict]:
        """
        Fetch annual financials BEFORE the given date.
        Returns 5+ years of data if available.
        """
        ticker = yf.Ticker(symbol)

        income = ticker.income_stmt
        balance = ticker.balance_sheet
        cashflow = ticker.cashflow

        if income.empty:
            return []

        records = []
        for col in income.columns:
            year_end = pd.to_datetime(col)

            # Point-in-time check: 90-day filing delay
            report_date = year_end + timedelta(days=90)
            if report_date >= before_date:
                continue

            record = self._extract_year(
                year_end,
                income[col] if col in income.columns else None,
                balance[col] if col in balance.columns else None,
                cashflow[col] if col in cashflow.columns else None
            )

            if record:
                records.append(record)

        return sorted(records, key=lambda x: x["fiscal_year"])[-5:]  # Last 5 years

    def fetch_prices(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> list[dict]:
        """Fetch split-adjusted daily prices."""
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start, end=end, auto_adjust=True)

        return [
            {"date": idx.date(), "adj_close": round(row["Close"], 4), "volume": int(row["Volume"])}
            for idx, row in hist.iterrows()
        ]

    def _extract_year(self, year_end, income, balance, cashflow) -> Optional[dict]:
        """Extract one year of normalized financial data."""

        def get(series, *keys):
            if series is None:
                return None
            for k in keys:
                if k in series.index and pd.notna(series[k]):
                    return float(series[k])
            return None

        revenue = get(income, "Total Revenue", "Revenue")
        if not revenue:
            return None

        gross_profit = get(income, "Gross Profit")
        operating_income = get(income, "Operating Income", "EBIT")
        ebitda = get(income, "EBITDA", "Normalized EBITDA")
        net_income = get(income, "Net Income", "Net Income Common Stockholders")

        total_debt = get(balance, "Total Debt", "Long Term Debt")
        cash = get(balance, "Cash And Cash Equivalents", "Cash")

        op_cf = get(cashflow, "Operating Cash Flow")
        capex = get(cashflow, "Capital Expenditure")
        fcf = (op_cf - abs(capex)) if op_cf and capex else None

        return {
            "fiscal_year": year_end.year,
            "report_date": (year_end + timedelta(days=90)).date(),
            "revenue": revenue / self.MILLION,
            "gross_profit": gross_profit / self.MILLION if gross_profit else None,
            "operating_income": operating_income / self.MILLION if operating_income else None,
            "ebitda": ebitda / self.MILLION if ebitda else None,
            "net_income": net_income / self.MILLION if net_income else None,
            "gross_margin": gross_profit / revenue if gross_profit else None,
            "operating_margin": operating_income / revenue if operating_income else None,
            "net_margin": net_income / revenue if net_income else None,
            "total_debt": total_debt / self.MILLION if total_debt else None,
            "cash_and_equivalents": cash / self.MILLION if cash else None,
            "operating_cash_flow": op_cf / self.MILLION if op_cf else None,
            "capital_expenditures": abs(capex) / self.MILLION if capex else None,
            "free_cash_flow": fcf / self.MILLION if fcf else None,
        }

    def _classify_market_cap(self, cap: int) -> str:
        if cap >= 10_000_000_000:
            return "large"
        elif cap >= 2_000_000_000:
            return "mid"
        return "small"
```

#### 2.3 Snapshot Generator
**scripts/services/snapshot_generator.py:**
```python
from datetime import datetime, timedelta
from typing import Optional

def generate_snapshots(
    stock_id: int,
    prices: list[dict],
    min_history_years: int = 5,
    forward_months: int = 24
) -> list[dict]:
    """
    Generate valid snapshot dates for a stock.
    Returns list of snapshot records with computed outcomes.
    """
    if not prices:
        return []

    # Sort prices by date
    prices = sorted(prices, key=lambda p: p["date"])

    first_date = prices[0]["date"]
    last_date = prices[-1]["date"]

    # Calculate valid snapshot window
    earliest = first_date + timedelta(days=min_history_years * 365)
    latest = last_date - timedelta(days=forward_months * 30)

    if earliest >= latest:
        return []

    snapshots = []
    current = earliest

    while current <= latest:
        outcome = compute_outcome(prices, current, forward_months)

        if outcome:
            snapshots.append({
                "stock_id": stock_id,
                "snapshot_date": current,
                **outcome
            })

        # Move to next quarter
        current = current + timedelta(days=90)

    return snapshots


def compute_outcome(
    prices: list[dict],
    snapshot_date: datetime,
    forward_months: int = 24
) -> Optional[dict]:
    """Calculate forward returns from a snapshot date."""

    def get_price(target: datetime) -> Optional[float]:
        for p in prices:
            if p["date"] >= target.date():
                return p["adj_close"]
        return None

    t0_price = get_price(snapshot_date)
    t6_price = get_price(snapshot_date + timedelta(days=182))
    t12_price = get_price(snapshot_date + timedelta(days=365))
    t24_price = get_price(snapshot_date + timedelta(days=forward_months * 30))

    if not t0_price or not t24_price:
        return None

    return_24mo = (t24_price / t0_price) - 1

    return {
        "price_at_snapshot": t0_price,
        "price_at_6mo": t6_price,
        "price_at_12mo": t12_price,
        "price_at_24mo": t24_price,
        "return_6mo": (t6_price / t0_price - 1) if t6_price else None,
        "return_12mo": (t12_price / t0_price - 1) if t12_price else None,
        "return_24mo": return_24mo,
        "outcome_label": classify_outcome(return_24mo),
        "difficulty": classify_difficulty(return_24mo)
    }


def classify_outcome(return_24mo: float) -> str:
    if return_24mo >= 0.30:
        return "value"
    elif return_24mo <= -0.20:
        return "trap"
    return "neutral"


def classify_difficulty(return_24mo: float) -> str:
    abs_return = abs(return_24mo)
    if abs_return >= 0.50:
        return "easy"  # Obvious outcomes
    elif abs_return <= 0.10:
        return "hard"  # Close calls
    return "medium"
```

#### 2.4 Fake Name Generator
**scripts/services/fake_names.py:**
```python
import random

SECTOR_PREFIXES = {
    "Technology": ["Tech", "Digital", "Cyber", "Cloud", "Data"],
    "Healthcare": ["Med", "Health", "Bio", "Pharma", "Care"],
    "Consumer Discretionary": ["Retail", "Consumer", "Lifestyle", "Brand"],
    "Financials": ["Capital", "Finance", "Asset", "Trust"],
    "Energy": ["Power", "Energy", "Fuel", "Resource"],
    "Industrials": ["Industrial", "Manufacturing", "Engineering"],
    "Materials": ["Material", "Chemical", "Mining"],
    "Utilities": ["Utility", "Grid", "Service"],
    "Real Estate": ["Property", "Realty", "Estate"],
    "Communication Services": ["Media", "Telecom", "Network"],
    "Consumer Staples": ["Staple", "Essential", "Daily"],
}

SUFFIXES = ["Alpha", "Beta", "Delta", "Gamma", "Omega", "Prime", "Core", "One", "X", "Plus"]
GENERIC = ["Corp", "Co", "Inc", "Group", "Holdings", "Enterprises"]

def generate_fake_name(sector: str, used_names: set[str]) -> str:
    """Generate a unique fake company name based on sector."""

    prefixes = SECTOR_PREFIXES.get(sector, ["Company"])

    for _ in range(100):  # Max attempts
        prefix = random.choice(prefixes)
        suffix = random.choice(SUFFIXES)
        generic = random.choice(GENERIC)

        # Try different formats
        formats = [
            f"{prefix} {suffix}",
            f"{prefix} {suffix} {generic}",
            f"The {prefix} {generic}",
            f"{suffix} {prefix}",
        ]

        name = random.choice(formats)
        if name not in used_names:
            return name

    # Fallback with UUID suffix
    import uuid
    return f"Company {str(uuid.uuid4())[:4].upper()}"
```

### Verification
- [ ] Database initializes with all tables
- [ ] Can fetch financials for test ticker (AAPL)
- [ ] Snapshots generate with correct outcome labels
- [ ] Fake names are unique per stock

---

## Phase 3: Core Game API

### Goals
- Build FastAPI endpoints for game flow
- Implement data retrieval and transformation
- Add admin endpoints for seeding

### Tasks

#### 3.1 Pydantic Models
**scripts/models/schemas.py:**
```python
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class FinancialYear(BaseModel):
    fiscal_year: int
    revenue: Optional[float]
    gross_margin: Optional[float]
    operating_income: Optional[float]
    ebitda: Optional[float]
    net_income: Optional[float]
    free_cash_flow: Optional[float]
    total_debt: Optional[float]
    cash_and_equivalents: Optional[float]

class GameSnapshot(BaseModel):
    snapshot_id: int
    fake_name: str
    sector: str
    industry: Optional[str]
    snapshot_date: date
    snapshot_year: int
    financials: list[FinancialYear]
    narrative: Optional[str]

class PricePoint(BaseModel):
    date: date
    price: float

class RevealResponse(BaseModel):
    ticker: str
    company_name: str
    snapshot_date: date
    price_at_snapshot: float
    price_at_24mo: float
    return_24mo: float
    outcome_label: str
    player_choice: str
    is_correct: bool
    price_series: list[PricePoint]

class SeedRequest(BaseModel):
    tickers: list[str]
    force_refresh: bool = False

class SeedResult(BaseModel):
    ticker: str
    success: bool
    snapshots_created: int
    error: Optional[str]
```

#### 3.2 Game Router
**scripts/api/game.py:**
```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models.schemas import GameSnapshot, RevealResponse
from services.database import get_db

router = APIRouter()

@router.get("/next", response_model=GameSnapshot)
async def get_next_snapshot(
    difficulty: Optional[str] = None,
    sector: Optional[str] = None,
    exclude_ids: Optional[str] = Query(None, description="Comma-separated snapshot IDs to exclude")
):
    """Get a random playable snapshot."""

    db = await get_db()

    # Build query with filters
    query = """
        SELECT s.id, s.snapshot_date, s.narrative,
               st.fake_name, st.sector, st.industry, st.id as stock_id
        FROM snapshots s
        JOIN stocks st ON s.stock_id = st.id
        WHERE st.is_active = 1
          AND s.outcome_label IN ('value', 'trap')
    """
    params = []

    if difficulty:
        query += " AND s.difficulty = ?"
        params.append(difficulty)

    if sector:
        query += " AND st.sector = ?"
        params.append(sector)

    if exclude_ids:
        ids = [int(x) for x in exclude_ids.split(",")]
        placeholders = ",".join("?" * len(ids))
        query += f" AND s.id NOT IN ({placeholders})"
        params.extend(ids)

    query += " ORDER BY RANDOM() LIMIT 1"

    async with db.execute(query, params) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(404, "No snapshots available")

    snapshot_id, snapshot_date, narrative, fake_name, sector, industry, stock_id = row

    # Get financials
    financials = await get_financials_for_snapshot(db, stock_id, snapshot_date)

    await db.close()

    return GameSnapshot(
        snapshot_id=snapshot_id,
        fake_name=fake_name,
        sector=sector or "Unknown",
        industry=industry,
        snapshot_date=snapshot_date,
        snapshot_year=snapshot_date.year,
        financials=financials,
        narrative=narrative
    )


@router.post("/reveal/{snapshot_id}", response_model=RevealResponse)
async def reveal_outcome(snapshot_id: int, player_choice: str):
    """Reveal the outcome for a snapshot."""

    if player_choice not in ("value", "trap"):
        raise HTTPException(400, "Choice must be 'value' or 'trap'")

    db = await get_db()

    # Get snapshot and stock data
    query = """
        SELECT s.*, st.ticker, st.company_name
        FROM snapshots s
        JOIN stocks st ON s.stock_id = st.id
        WHERE s.id = ?
    """
    async with db.execute(query, [snapshot_id]) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(404, "Snapshot not found")

    # Parse row into dict (aiosqlite returns tuples)
    columns = [d[0] for d in cursor.description]
    snapshot = dict(zip(columns, row))

    # Get price series for chart
    price_query = """
        SELECT date, adj_close
        FROM price_history
        WHERE stock_id = ?
          AND date >= ?
          AND date <= date(?, '+24 months')
        ORDER BY date
    """
    async with db.execute(price_query, [
        snapshot["stock_id"],
        snapshot["snapshot_date"],
        snapshot["snapshot_date"]
    ]) as cursor:
        price_rows = await cursor.fetchall()

    # Determine if correct
    is_correct = (
        (player_choice == "value" and snapshot["outcome_label"] == "value") or
        (player_choice == "trap" and snapshot["outcome_label"] == "trap")
    )

    # Update play stats
    await db.execute("""
        UPDATE snapshots
        SET times_played = times_played + 1,
            correct_guesses = correct_guesses + ?
        WHERE id = ?
    """, [1 if is_correct else 0, snapshot_id])
    await db.commit()
    await db.close()

    return RevealResponse(
        ticker=snapshot["ticker"],
        company_name=snapshot["company_name"],
        snapshot_date=snapshot["snapshot_date"],
        price_at_snapshot=snapshot["price_at_snapshot"],
        price_at_24mo=snapshot["price_at_24mo"],
        return_24mo=snapshot["return_24mo"],
        outcome_label=snapshot["outcome_label"],
        player_choice=player_choice,
        is_correct=is_correct,
        price_series=[
            {"date": row[0], "price": row[1]}
            for row in price_rows
        ]
    )


async def get_financials_for_snapshot(db, stock_id: int, snapshot_date) -> list:
    """Get 5 years of financials before snapshot date."""
    query = """
        SELECT fiscal_year, revenue, gross_margin, operating_income,
               ebitda, net_income, free_cash_flow, total_debt, cash_and_equivalents
        FROM financials
        WHERE stock_id = ?
          AND report_date <= ?
        ORDER BY fiscal_year DESC
        LIMIT 5
    """
    async with db.execute(query, [stock_id, snapshot_date]) as cursor:
        rows = await cursor.fetchall()

    return [
        {
            "fiscal_year": row[0],
            "revenue": row[1],
            "gross_margin": row[2],
            "operating_income": row[3],
            "ebitda": row[4],
            "net_income": row[5],
            "free_cash_flow": row[6],
            "total_debt": row[7],
            "cash_and_equivalents": row[8],
        }
        for row in reversed(rows)  # Chronological order
    ]
```

#### 3.3 Admin Router
**scripts/api/admin.py:**
```python
from fastapi import APIRouter, BackgroundTasks
from models.schemas import SeedRequest, SeedResult
from services.extractor import YFinanceExtractor
from services.snapshot_generator import generate_snapshots
from services.fake_names import generate_fake_name
from services.database import get_db
from datetime import datetime

router = APIRouter()

@router.post("/seed")
async def seed_database(request: SeedRequest, background_tasks: BackgroundTasks):
    """Seed database with stock data. Runs in background."""
    background_tasks.add_task(seed_tickers, request.tickers, request.force_refresh)
    return {"message": f"Seeding {len(request.tickers)} tickers in background"}


async def seed_tickers(tickers: list[str], force_refresh: bool):
    """Background task to seed ticker data."""
    extractor = YFinanceExtractor()
    db = await get_db()

    # Get existing fake names
    async with db.execute("SELECT fake_name FROM stocks") as cursor:
        used_names = {row[0] for row in await cursor.fetchall()}

    results = []

    for ticker in tickers:
        try:
            result = await seed_single_ticker(
                db, extractor, ticker, used_names, force_refresh
            )
            results.append(result)
            if result["success"]:
                used_names.add(result.get("fake_name", ""))
        except Exception as e:
            results.append({
                "ticker": ticker,
                "success": False,
                "error": str(e)
            })

    await db.close()
    return results


async def seed_single_ticker(db, extractor, ticker: str, used_names: set, force: bool):
    """Seed a single ticker's data."""

    # Check if exists
    async with db.execute(
        "SELECT id FROM stocks WHERE ticker = ?", [ticker]
    ) as cursor:
        existing = await cursor.fetchone()

    if existing and not force:
        return {"ticker": ticker, "success": True, "snapshots_created": 0, "note": "Already exists"}

    # Fetch company info
    info = extractor.fetch_company_info(ticker)
    if not info["company_name"]:
        return {"ticker": ticker, "success": False, "error": "Company not found"}

    # Generate fake name
    fake_name = generate_fake_name(info["sector"], used_names)

    # Insert or update stock
    await db.execute("""
        INSERT INTO stocks (ticker, company_name, fake_name, sector, industry, market_cap_tier)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            company_name = excluded.company_name,
            sector = excluded.sector,
            industry = excluded.industry,
            market_cap_tier = excluded.market_cap_tier
    """, [ticker, info["company_name"], fake_name, info["sector"], info["industry"], info["market_cap_tier"]])

    # Get stock ID
    async with db.execute("SELECT id FROM stocks WHERE ticker = ?", [ticker]) as cursor:
        stock_id = (await cursor.fetchone())[0]

    # Fetch price history (10 years)
    now = datetime.now()
    prices = extractor.fetch_prices(
        ticker,
        datetime(now.year - 10, 1, 1),
        now
    )

    # Insert prices
    for p in prices:
        await db.execute("""
            INSERT OR IGNORE INTO price_history (stock_id, date, adj_close, volume)
            VALUES (?, ?, ?, ?)
        """, [stock_id, p["date"], p["adj_close"], p["volume"]])

    # Fetch and insert financials
    financials = extractor.fetch_financials(ticker, now)
    for f in financials:
        await db.execute("""
            INSERT OR REPLACE INTO financials (
                stock_id, fiscal_year, report_date, revenue, gross_profit,
                operating_income, ebitda, net_income, gross_margin,
                operating_margin, net_margin, total_debt, cash_and_equivalents,
                operating_cash_flow, capital_expenditures, free_cash_flow
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            stock_id, f["fiscal_year"], f["report_date"], f.get("revenue"),
            f.get("gross_profit"), f.get("operating_income"), f.get("ebitda"),
            f.get("net_income"), f.get("gross_margin"), f.get("operating_margin"),
            f.get("net_margin"), f.get("total_debt"), f.get("cash_and_equivalents"),
            f.get("operating_cash_flow"), f.get("capital_expenditures"), f.get("free_cash_flow")
        ])

    # Generate snapshots
    snapshots = generate_snapshots(stock_id, prices)

    for s in snapshots:
        await db.execute("""
            INSERT OR IGNORE INTO snapshots (
                stock_id, snapshot_date, price_at_snapshot, price_at_6mo,
                price_at_12mo, price_at_24mo, return_6mo, return_12mo,
                return_24mo, outcome_label, difficulty
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            s["stock_id"], s["snapshot_date"], s["price_at_snapshot"],
            s.get("price_at_6mo"), s.get("price_at_12mo"), s["price_at_24mo"],
            s.get("return_6mo"), s.get("return_12mo"), s["return_24mo"],
            s["outcome_label"], s["difficulty"]
        ])

    await db.commit()

    return {
        "ticker": ticker,
        "success": True,
        "snapshots_created": len(snapshots),
        "fake_name": fake_name
    }
```

### Verification
- [ ] `GET /game/next` returns valid snapshot
- [ ] `POST /game/reveal/{id}` returns correct outcome
- [ ] `POST /admin/seed` successfully populates database
- [ ] Filtering by difficulty/sector works

---

## Phase 4: Blazor Foundation

### Goals
- Set up basic Blazor structure
- Configure MudBlazor theme
- Create routing and layout

### Tasks

#### 4.1 App Layout
**app/Components/Layout/MainLayout.razor:**
```razor
@inherits LayoutComponentBase

<MudThemeProvider Theme="@_theme" IsDarkMode="true" />
<MudPopoverProvider />
<MudDialogProvider />
<MudSnackbarProvider />

<MudLayout>
    <MudAppBar Elevation="0" Dense="true" Color="Color.Transparent">
        <MudText Typo="Typo.h6" Class="ml-3">Trap Or Value</MudText>
        <MudSpacer />
        <MudIconButton Icon="@Icons.Material.Filled.Leaderboard" Color="Color.Inherit" />
        <MudIconButton Icon="@Icons.Material.Filled.Settings" Color="Color.Inherit" />
    </MudAppBar>

    <MudMainContent Class="pt-16 px-4">
        @Body
    </MudMainContent>
</MudLayout>

@code {
    private MudTheme _theme = new MudTheme {
        PaletteDark = new PaletteDark {
            Black = "#0D1117",
            Background = "#0D1117",
            BackgroundGrey = "#161B22",
            Surface = "#161B22",
            DrawerBackground = "#161B22",
            DrawerText = "rgba(255,255,255, 0.70)",
            AppbarBackground = "#161B22",
            AppbarText = "rgba(255,255,255, 0.70)",
            TextPrimary = "#E6EDF3",
            TextSecondary = "#8B949E",
            ActionDefault = "#8B949E",
            ActionDisabled = "rgba(255,255,255, 0.26)",
            ActionDisabledBackground = "rgba(255,255,255, 0.12)",
            Success = "#3FB950",
            Error = "#F85149",
            Warning = "#D29922",
            Info = "#58A6FF",
            Primary = "#58A6FF",
            Secondary = "#8B949E"
        },
        Typography = new Typography {
            Default = new Default {
                FontFamily = new[] { "Inter", "-apple-system", "sans-serif" }
            }
        }
    };
}
```

#### 4.2 Game Page
**app/Components/Pages/Game.razor:**
```razor
@page "/"
@page "/game"
@inject GameStateService GameState
@implements IDisposable

<PageTitle>Trap Or Value</PageTitle>

<MudContainer MaxWidth="MaxWidth.Large" Class="mt-4">
    @switch (GameState.CurrentState)
    {
        case GameState.Loading:
            <LoadingState />
            break;

        case GameState.Analyzing:
            <AnalyzingState
                Snapshot="GameState.CurrentSnapshot"
                OnDecision="HandleDecision" />
            break;

        case GameState.Revealing:
            <RevealingState Choice="@GameState.PlayerChoice" />
            break;

        case GameState.Result:
            <ResultState
                Reveal="GameState.CurrentReveal"
                OnPlayAgain="HandlePlayAgain" />
            break;
    }
</MudContainer>

@code {
    protected override async Task OnInitializedAsync()
    {
        GameState.OnStateChanged += StateHasChanged;
        await GameState.LoadNextSnapshot();
    }

    private async Task HandleDecision(string choice)
    {
        await GameState.MakeDecision(choice);
    }

    private async Task HandlePlayAgain()
    {
        await GameState.PlayAgain();
    }

    public void Dispose()
    {
        GameState.OnStateChanged -= StateHasChanged;
    }
}
```

#### 4.3 Game Service
**app/Services/GameService.cs:**
```csharp
using System.Net.Http.Json;

public class GameService
{
    private readonly HttpClient _httpClient;

    public GameService(IHttpClientFactory factory)
    {
        _httpClient = factory.CreateClient("PythonApi");
    }

    public async Task<SnapshotData> GetNextSnapshotAsync(
        string? difficulty = null,
        string? sector = null,
        int[]? excludeIds = null)
    {
        var query = new List<string>();
        if (difficulty != null) query.Add($"difficulty={difficulty}");
        if (sector != null) query.Add($"sector={sector}");
        if (excludeIds?.Any() == true) query.Add($"exclude_ids={string.Join(",", excludeIds)}");

        var url = "/game/next" + (query.Any() ? "?" + string.Join("&", query) : "");
        return await _httpClient.GetFromJsonAsync<SnapshotData>(url)
            ?? throw new Exception("Failed to fetch snapshot");
    }

    public async Task<RevealData> RevealOutcomeAsync(int snapshotId, string choice)
    {
        var response = await _httpClient.PostAsJsonAsync(
            $"/game/reveal/{snapshotId}",
            new { player_choice = choice }
        );
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<RevealData>()
            ?? throw new Exception("Failed to reveal outcome");
    }
}
```

### Verification
- [ ] App loads with dark theme
- [ ] Navigation works
- [ ] Game state transitions correctly
- [ ] API calls succeed from Blazor

---

## Phase 5: Game UI Components

### Goals
- Build all game components from ui-ux.md spec
- Implement swipe functionality
- Create financial table and result view

### Tasks

#### 5.1 Financial Table Component
#### 5.2 Company Card Component
#### 5.3 Narrative Panel Component
#### 5.4 Swipe Card Component
#### 5.5 Result View with Chart
#### 5.6 Loading/Revealing States

*Implementation follows specifications in ui-ux.md*

---

## Phase 6: AI Narrative Integration

### Goals
- Integrate Gemini via Microsoft.Extensions.AI
- Create point-in-time aware prompts
- Generate and cache narratives

### Tasks

#### 6.1 Gemini Service
**app/Services/GeminiService.cs:**
```csharp
using Microsoft.Extensions.AI;

public class GeminiService
{
    private readonly IChatClient _chatClient;

    public GeminiService(IChatClient chatClient)
    {
        _chatClient = chatClient;
    }

    public async Task<string> GenerateNarrativeAsync(
        string sector,
        DateTime snapshotDate,
        List<FinancialYear> financials)
    {
        var prompt = BuildPrompt(sector, snapshotDate, financials);

        var response = await _chatClient.CompleteAsync(prompt);
        return response.Message.Text ?? "Analysis unavailable.";
    }

    private string BuildPrompt(string sector, DateTime date, List<FinancialYear> financials)
    {
        var year = date.Year;
        var month = date.ToString("MMMM");

        var financialSummary = string.Join("\n", financials.Select(f =>
            $"- {f.FiscalYear}: Revenue ${f.Revenue:N1}M, Net Income ${f.NetIncome:N1}M"
        ));

        return $"""
        You are a value investing analyst writing in {month} {year}.
        You must NOT reference any events after {date:MMMM yyyy}.

        Analyze this {sector} company based on the following financials:
        {financialSummary}

        Write a 3-paragraph analysis:
        1. Current state: Describe the company's situation AT THIS TIME ({month} {year})
        2. Bull case: What optimists believe could happen
        3. Bear case: What pessimists fear could happen

        Rules:
        - Do NOT mention the company name or ticker
        - Use present tense ("The company is..." not "The company was...")
        - Be specific about the numbers
        - Keep it under 200 words total
        """;
    }
}
```

#### 6.2 Narrative Generation Endpoint
#### 6.3 Caching Layer

---

## Phase 7: Polish & Testing

### Goals
- Add animations and transitions
- Handle edge cases
- Performance optimization
- Unit and integration tests

### Tasks
- [ ] Implement typewriter effect
- [ ] Add swipe physics and haptics
- [ ] Result reveal animation sequence
- [ ] Loading skeleton states
- [ ] Error handling UI
- [ ] Offline support
- [ ] Unit tests for data pipeline
- [ ] Integration tests for API
- [ ] E2E tests for game flow

---

## Phase 8: Deployment

### Goals
- Production Docker configuration
- Environment setup
- Monitoring and logging

### Tasks
- [ ] Production Dockerfiles
- [ ] Environment variable management
- [ ] Health check endpoints
- [ ] Logging configuration
- [ ] Error tracking (Sentry)
- [ ] Analytics events
- [ ] CI/CD pipeline
- [ ] SSL/TLS setup

---

## Appendix: Command Reference

### Development
```bash
# Start all services
docker-compose up

# Seed database with initial stocks
curl -X POST http://localhost:8000/admin/seed \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT", "GME", "NVDA", "META"]}'

# Run Blazor in development
cd app && dotnet watch

# Run Python API in development
cd scripts && uvicorn main:app --reload
```

### Testing
```bash
# Python tests
cd scripts && pytest

# .NET tests
cd app && dotnet test

# E2E tests
npx playwright test
```