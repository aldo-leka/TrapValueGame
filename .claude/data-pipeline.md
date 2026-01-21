# Data Pipeline: Scraper, Aggregation & Storage

This document details how stock data flows from yfinance into SQLite, how we maintain point-in-time accuracy, and how the game API serves data.

---

## Table of Contents
1. [Database Schema](#database-schema)
2. [yfinance Data Extraction](#yfinance-data-extraction)
3. [Data Aggregation Logic](#data-aggregation-logic)
4. [Snapshot Generation](#snapshot-generation)
5. [API Endpoints](#api-endpoints)
6. [Caching Strategy](#caching-strategy)
7. [Error Handling](#error-handling)
8. [Data Quality Validation](#data-quality-validation)

---

## Database Schema

### `stocks` - Master Stock Registry
```sql
CREATE TABLE stocks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL UNIQUE,      -- Real ticker: "AAPL"
    company_name    TEXT NOT NULL,             -- Real name: "Apple Inc."
    fake_name       TEXT NOT NULL,             -- Game name: "Tech Giant Alpha"
    sector          TEXT,                      -- "Technology"
    industry        TEXT,                      -- "Consumer Electronics"
    market_cap_tier TEXT,                      -- "large", "mid", "small"
    is_active       BOOLEAN DEFAULT 1,         -- Soft delete flag
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### `financials` - Annual Financial Data
```sql
CREATE TABLE financials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id        INTEGER NOT NULL REFERENCES stocks(id),
    fiscal_year     INTEGER NOT NULL,          -- 2018
    report_date     DATE NOT NULL,             -- Actual filing date

    -- Income Statement (in millions USD)
    revenue         REAL,
    gross_profit    REAL,
    operating_income REAL,
    ebitda          REAL,
    net_income      REAL,

    -- Margins (stored as decimals: 0.25 = 25%)
    gross_margin    REAL,
    operating_margin REAL,
    net_margin      REAL,

    -- Balance Sheet
    total_assets    REAL,
    total_debt      REAL,
    cash_and_equivalents REAL,
    total_equity    REAL,

    -- Cash Flow
    operating_cash_flow REAL,
    capital_expenditures REAL,
    free_cash_flow  REAL,

    -- Per Share & Valuation
    shares_outstanding REAL,                   -- In millions
    earnings_per_share REAL,
    book_value_per_share REAL,

    UNIQUE(stock_id, fiscal_year)
);
```

### `price_history` - Daily Adjusted Prices
```sql
CREATE TABLE price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id        INTEGER NOT NULL REFERENCES stocks(id),
    date            DATE NOT NULL,
    adj_close       REAL NOT NULL,             -- Split-adjusted price
    volume          INTEGER,

    UNIQUE(stock_id, date)
);
```

### `snapshots` - Game Scenarios
```sql
CREATE TABLE snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id        INTEGER NOT NULL REFERENCES stocks(id),
    snapshot_date   DATE NOT NULL,             -- T-0: The "present" in the game

    -- Pre-computed outcome data
    price_at_snapshot   REAL NOT NULL,
    price_at_6mo        REAL,                  -- T+6 months
    price_at_12mo       REAL,                  -- T+12 months
    price_at_24mo       REAL NOT NULL,         -- T+24 months (primary outcome)

    -- Calculated returns (decimals)
    return_6mo      REAL,
    return_12mo     REAL,
    return_24mo     REAL NOT NULL,

    -- AI-generated content
    narrative       TEXT,                      -- Gemini-generated story
    narrative_generated_at DATETIME,

    -- Classification
    outcome_label   TEXT,                      -- "value", "trap", "neutral"
    difficulty      TEXT,                      -- "easy", "medium", "hard"

    -- Usage tracking
    times_played    INTEGER DEFAULT 0,
    correct_guesses INTEGER DEFAULT 0,

    UNIQUE(stock_id, snapshot_date)
);
```

### `game_sessions` - Player History
```sql
CREATE TABLE game_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,             -- UUID for anonymous tracking
    snapshot_id     INTEGER NOT NULL REFERENCES snapshots(id),
    player_choice   TEXT NOT NULL,             -- "value" or "trap"
    is_correct      BOOLEAN,
    played_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## yfinance Data Extraction

### Core Extraction Function

```python
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

class YFinanceExtractor:
    """Extracts and normalizes data from yfinance."""

    def __init__(self, cache_dir: str = "/shared/cache"):
        self.cache_dir = cache_dir

    def get_ticker(self, symbol: str) -> yf.Ticker:
        """Get ticker with caching enabled."""
        return yf.Ticker(symbol)

    def fetch_company_info(self, symbol: str) -> dict:
        """Extract static company information."""
        ticker = self.get_ticker(symbol)
        info = ticker.info

        return {
            "ticker": symbol,
            "company_name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap_tier": self._classify_market_cap(info.get("marketCap", 0))
        }

    def fetch_financials(
        self,
        symbol: str,
        before_date: datetime
    ) -> list[dict]:
        """
        Fetch annual financials for years BEFORE the snapshot date.

        CRITICAL: Only returns data where report_date < before_date
        to maintain point-in-time integrity.
        """
        ticker = self.get_ticker(symbol)

        # Get all available financial statements
        income_stmt = ticker.income_stmt          # Annual
        balance_sheet = ticker.balance_sheet      # Annual
        cash_flow = ticker.cashflow               # Annual

        financials = []

        # Income statement columns are fiscal year end dates
        for col in income_stmt.columns:
            fiscal_year_end = pd.to_datetime(col)

            # POINT-IN-TIME CHECK: Skip future data
            # Add 90-day buffer for filing delay (10-K deadline)
            estimated_report_date = fiscal_year_end + timedelta(days=90)
            if estimated_report_date >= before_date:
                continue

            record = self._extract_year_data(
                fiscal_year_end,
                income_stmt[col] if col in income_stmt.columns else None,
                balance_sheet[col] if col in balance_sheet.columns else None,
                cash_flow[col] if col in cash_flow.columns else None
            )

            if record:
                financials.append(record)

        return sorted(financials, key=lambda x: x["fiscal_year"])

    def fetch_price_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> list[dict]:
        """
        Fetch split-adjusted daily prices.

        CRITICAL: Always use auto_adjust=True to handle splits correctly.
        """
        ticker = self.get_ticker(symbol)

        hist = ticker.history(
            start=start_date,
            end=end_date,
            auto_adjust=True,    # <-- MANDATORY for split accuracy
            actions=False
        )

        prices = []
        for date, row in hist.iterrows():
            prices.append({
                "date": date.date(),
                "adj_close": round(row["Close"], 4),
                "volume": int(row["Volume"])
            })

        return prices

    def _extract_year_data(
        self,
        fiscal_year_end: datetime,
        income: Optional[pd.Series],
        balance: Optional[pd.Series],
        cashflow: Optional[pd.Series]
    ) -> Optional[dict]:
        """Extract and normalize one year of financial data."""

        def safe_get(series, *keys):
            """Try multiple possible key names."""
            if series is None:
                return None
            for key in keys:
                if key in series.index:
                    val = series[key]
                    if pd.notna(val):
                        return float(val)
            return None

        # All values normalized to millions
        MILLION = 1_000_000

        revenue = safe_get(income, "Total Revenue", "Revenue")
        gross_profit = safe_get(income, "Gross Profit")
        operating_income = safe_get(income, "Operating Income", "EBIT")
        ebitda = safe_get(income, "EBITDA", "Normalized EBITDA")
        net_income = safe_get(income, "Net Income", "Net Income Common Stockholders")

        total_assets = safe_get(balance, "Total Assets")
        total_debt = safe_get(balance, "Total Debt", "Long Term Debt")
        cash = safe_get(balance, "Cash And Cash Equivalents", "Cash")
        total_equity = safe_get(balance, "Total Equity Gross Minority Interest", "Stockholders Equity")

        op_cf = safe_get(cashflow, "Operating Cash Flow", "Cash Flow From Operating Activities")
        capex = safe_get(cashflow, "Capital Expenditure", "Capital Expenditures")

        # Skip if missing critical data
        if revenue is None:
            return None

        # Calculate derived metrics
        gross_margin = (gross_profit / revenue) if gross_profit and revenue else None
        operating_margin = (operating_income / revenue) if operating_income and revenue else None
        net_margin = (net_income / revenue) if net_income and revenue else None
        fcf = (op_cf - abs(capex)) if op_cf and capex else None

        return {
            "fiscal_year": fiscal_year_end.year,
            "report_date": (fiscal_year_end + timedelta(days=90)).date(),

            # Normalize to millions
            "revenue": revenue / MILLION if revenue else None,
            "gross_profit": gross_profit / MILLION if gross_profit else None,
            "operating_income": operating_income / MILLION if operating_income else None,
            "ebitda": ebitda / MILLION if ebitda else None,
            "net_income": net_income / MILLION if net_income else None,

            "gross_margin": round(gross_margin, 4) if gross_margin else None,
            "operating_margin": round(operating_margin, 4) if operating_margin else None,
            "net_margin": round(net_margin, 4) if net_margin else None,

            "total_assets": total_assets / MILLION if total_assets else None,
            "total_debt": total_debt / MILLION if total_debt else None,
            "cash_and_equivalents": cash / MILLION if cash else None,
            "total_equity": total_equity / MILLION if total_equity else None,

            "operating_cash_flow": op_cf / MILLION if op_cf else None,
            "capital_expenditures": abs(capex) / MILLION if capex else None,
            "free_cash_flow": fcf / MILLION if fcf else None,
        }

    def _classify_market_cap(self, market_cap: int) -> str:
        """Classify by market cap tier."""
        if market_cap >= 10_000_000_000:  # $10B+
            return "large"
        elif market_cap >= 2_000_000_000:  # $2B+
            return "mid"
        else:
            return "small"
```

---

## Data Aggregation Logic

### Metrics We Display (TIKR-style table)

| Metric | Source | Calculation | Display Format |
|--------|--------|-------------|----------------|
| **Revenue** | income_stmt | Direct | `$1,234.5M` |
| **Gross Margin %** | Calculated | `gross_profit / revenue` | `45.2%` |
| **Operating Income** | income_stmt | Direct | `$234.5M` |
| **EBITDA** | income_stmt | Direct or calculated | `$345.6M` |
| **Net Income** | income_stmt | Direct | `$123.4M` or `(45.6M)` |
| **Free Cash Flow** | Calculated | `operating_cf - capex` | `$89.0M` |
| **Total Debt** | balance_sheet | Direct | `$500.0M` |
| **Cash & Equiv.** | balance_sheet | Direct | `$200.0M` |
| **Shares Outstanding** | info/balance | Direct | `45.2M` |

### Year-over-Year Calculations (for visual indicators)

```python
def calculate_yoy_changes(financials: list[dict]) -> list[dict]:
    """Add YoY change percentages for trend arrows."""

    if len(financials) < 2:
        return financials

    result = []
    for i, current in enumerate(financials):
        enriched = current.copy()

        if i > 0:
            previous = financials[i - 1]

            # Calculate YoY for key metrics
            for metric in ["revenue", "ebitda", "net_income", "free_cash_flow"]:
                curr_val = current.get(metric)
                prev_val = previous.get(metric)

                if curr_val and prev_val and prev_val != 0:
                    yoy = (curr_val - prev_val) / abs(prev_val)
                    enriched[f"{metric}_yoy"] = round(yoy, 4)

        result.append(enriched)

    return result
```

### Handling Missing Data

```python
DISPLAY_RULES = {
    "revenue": {"required": True, "fallback": None},
    "gross_margin": {"required": False, "fallback": "N/A"},
    "ebitda": {"required": False, "fallback": "N/A"},
    "net_income": {"required": True, "fallback": None},
    "free_cash_flow": {"required": False, "fallback": "N/A"},
    "total_debt": {"required": False, "fallback": "$0.0M"},
    "cash_and_equivalents": {"required": False, "fallback": "N/A"},
}

def format_financial_value(value, metric_name: str) -> str:
    """Format a financial value for display."""
    rules = DISPLAY_RULES.get(metric_name, {})

    if value is None:
        return rules.get("fallback", "N/A")

    # Handle negative values with brackets
    if value < 0:
        return f"(${abs(value):,.1f}M)"

    return f"${value:,.1f}M"
```

---

## Snapshot Generation

### Selecting Snapshot Dates

```python
from datetime import datetime, timedelta
import random

def generate_snapshot_dates(
    stock_id: int,
    data_start: datetime,
    data_end: datetime,
    min_gap_days: int = 365
) -> list[datetime]:
    """
    Generate valid snapshot dates for a stock.

    Requirements:
    - At least 5 years of data before snapshot
    - At least 2 years of data after snapshot
    - Snapshots spaced at least 1 year apart
    """

    earliest_snapshot = data_start + timedelta(days=5*365)
    latest_snapshot = data_end - timedelta(days=2*365)

    if earliest_snapshot >= latest_snapshot:
        return []  # Not enough data

    # Generate potential dates (first trading day of each quarter)
    snapshots = []
    current = earliest_snapshot

    while current <= latest_snapshot:
        # Snap to first of quarter
        quarter_month = ((current.month - 1) // 3) * 3 + 1
        snapshot_date = datetime(current.year, quarter_month, 1)

        if earliest_snapshot <= snapshot_date <= latest_snapshot:
            snapshots.append(snapshot_date)

        current += timedelta(days=min_gap_days)

    return snapshots
```

### Computing Outcomes

```python
def compute_snapshot_outcome(
    prices: list[dict],
    snapshot_date: datetime
) -> dict:
    """
    Calculate forward returns from a snapshot date.

    Returns prices and returns at 6mo, 12mo, and 24mo.
    """

    def get_price_at_date(target_date: datetime) -> Optional[float]:
        """Get closest price on or after target date."""
        for p in prices:
            if p["date"] >= target_date.date():
                return p["adj_close"]
        return None

    price_t0 = get_price_at_date(snapshot_date)
    price_6mo = get_price_at_date(snapshot_date + timedelta(days=182))
    price_12mo = get_price_at_date(snapshot_date + timedelta(days=365))
    price_24mo = get_price_at_date(snapshot_date + timedelta(days=730))

    if not price_t0 or not price_24mo:
        return None

    return {
        "price_at_snapshot": price_t0,
        "price_at_6mo": price_6mo,
        "price_at_12mo": price_12mo,
        "price_at_24mo": price_24mo,
        "return_6mo": (price_6mo / price_t0 - 1) if price_6mo else None,
        "return_12mo": (price_12mo / price_t0 - 1) if price_12mo else None,
        "return_24mo": (price_24mo / price_t0 - 1),
        "outcome_label": classify_outcome(price_24mo / price_t0 - 1)
    }

def classify_outcome(return_24mo: float) -> str:
    """Classify the outcome for game logic."""
    if return_24mo >= 0.30:      # +30% or more
        return "value"
    elif return_24mo <= -0.20:   # -20% or worse
        return "trap"
    else:
        return "neutral"
```

---

## API Endpoints

### `GET /game/next`
Returns a random playable snapshot with obfuscated data.

```python
@router.get("/game/next")
async def get_next_snapshot(
    difficulty: Optional[str] = None,
    sector: Optional[str] = None,
    exclude_ids: Optional[str] = None  # Comma-separated IDs
) -> GameSnapshot:
    """
    Response Schema:
    {
        "snapshot_id": 123,
        "fake_name": "Retailer X",
        "sector": "Consumer Discretionary",
        "snapshot_date": "2018-01-01",
        "snapshot_year": 2018,
        "financials": [
            {
                "fiscal_year": 2013,
                "revenue": 1234.5,
                "gross_margin": 0.452,
                ...
            },
            ... // 5 years of data
        ],
        "narrative": "It is January 2018. This retailer has seen..."
    }
    """
```

### `POST /game/reveal/{snapshot_id}`
Reveals the actual outcome after player makes choice.

```python
@router.post("/game/reveal/{snapshot_id}")
async def reveal_outcome(
    snapshot_id: int,
    player_choice: Literal["value", "trap"]
) -> RevealResponse:
    """
    Response Schema:
    {
        "ticker": "GME",
        "company_name": "GameStop Corp.",
        "snapshot_date": "2018-01-01",
        "price_at_snapshot": 18.50,
        "price_at_24mo": 4.20,
        "return_24mo": -0.773,
        "outcome_label": "trap",
        "player_choice": "trap",
        "is_correct": true,
        "price_series": [
            {"date": "2018-01-01", "price": 18.50},
            {"date": "2018-01-02", "price": 18.75},
            ... // Daily prices for 24 months
        ]
    }
    """
```

### `POST /admin/seed`
Populates database with stock data.

```python
@router.post("/admin/seed")
async def seed_database(
    tickers: list[str],
    force_refresh: bool = False
) -> SeedResponse:
    """
    For each ticker:
    1. Fetch company info
    2. Fetch 10+ years of financials
    3. Fetch price history
    4. Generate valid snapshot dates
    5. Compute outcomes for each snapshot
    """
```

---

## Caching Strategy

### yfinance Response Caching

```python
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

class YFinanceCache:
    """File-based cache for yfinance responses."""

    def __init__(self, cache_dir: str, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _cache_key(self, ticker: str, data_type: str) -> str:
        return f"{ticker}_{data_type}.json"

    def get(self, ticker: str, data_type: str) -> Optional[dict]:
        path = self.cache_dir / self._cache_key(ticker, data_type)

        if not path.exists():
            return None

        # Check TTL
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            return None

        with open(path) as f:
            return json.load(f)

    def set(self, ticker: str, data_type: str, data: dict):
        path = self.cache_dir / self._cache_key(ticker, data_type)
        with open(path, "w") as f:
            json.dump(data, f)
```

### Cache Invalidation Rules

| Data Type | TTL | Invalidation Trigger |
|-----------|-----|---------------------|
| Company Info | 7 days | Manual refresh |
| Financials | 24 hours | New fiscal year detected |
| Price History | 1 hour | Market hours only |
| Snapshots | Never | Manual regeneration |

---

## Error Handling

### Common yfinance Errors

```python
from enum import Enum

class DataError(Enum):
    TICKER_NOT_FOUND = "ticker_not_found"
    INSUFFICIENT_HISTORY = "insufficient_history"
    MISSING_FINANCIALS = "missing_financials"
    DELISTED = "delisted"
    API_RATE_LIMIT = "api_rate_limit"

def validate_ticker_data(symbol: str, extractor: YFinanceExtractor) -> tuple[bool, Optional[DataError]]:
    """
    Validate that a ticker has sufficient data for the game.
    """
    try:
        info = extractor.fetch_company_info(symbol)

        if not info.get("company_name"):
            return False, DataError.TICKER_NOT_FOUND

        # Check for delisting indicators
        if info.get("sector") is None and info.get("industry") is None:
            return False, DataError.DELISTED

        # Fetch financials
        financials = extractor.fetch_financials(
            symbol,
            datetime.now()
        )

        if len(financials) < 5:
            return False, DataError.INSUFFICIENT_HISTORY

        # Check for required fields
        required_fields = ["revenue", "net_income"]
        for f in financials:
            if not all(f.get(field) for field in required_fields):
                return False, DataError.MISSING_FINANCIALS

        return True, None

    except Exception as e:
        if "rate limit" in str(e).lower():
            return False, DataError.API_RATE_LIMIT
        raise
```

### Retry Logic

```python
import asyncio
from functools import wraps

def with_retry(max_attempts: int = 3, delay_seconds: float = 1.0):
    """Decorator for retrying yfinance calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay_seconds * (attempt + 1))
            raise last_error
        return wrapper
    return decorator
```

---

## Data Quality Validation

### Pre-Insertion Checks

```python
def validate_financial_record(record: dict) -> list[str]:
    """Return list of validation warnings."""
    warnings = []

    # Revenue sanity check
    if record.get("revenue") and record["revenue"] < 0:
        warnings.append("Negative revenue detected")

    # Margin bounds check
    for margin in ["gross_margin", "operating_margin", "net_margin"]:
        val = record.get(margin)
        if val and (val < -2.0 or val > 1.0):
            warnings.append(f"{margin} out of bounds: {val}")

    # Debt/Cash sanity
    if record.get("total_debt") and record["total_debt"] < 0:
        warnings.append("Negative debt (should be positive)")

    # FCF calculation verification
    if all(record.get(f) for f in ["operating_cash_flow", "capital_expenditures", "free_cash_flow"]):
        expected_fcf = record["operating_cash_flow"] - record["capital_expenditures"]
        if abs(expected_fcf - record["free_cash_flow"]) > 1.0:  # $1M tolerance
            warnings.append("FCF doesn't match OCF - CapEx")

    return warnings
```

### Snapshot Quality Score

```python
def score_snapshot_quality(snapshot: dict, financials: list[dict]) -> float:
    """
    Score 0-100 for how "good" a game scenario is.
    Higher = more interesting/educational.
    """
    score = 50.0  # Base score

    # Penalize neutral outcomes (boring)
    if snapshot["outcome_label"] == "neutral":
        score -= 20

    # Bonus for dramatic outcomes
    if abs(snapshot["return_24mo"]) > 0.5:
        score += 15

    # Bonus for complete financial data
    completeness = sum(1 for f in financials if f.get("ebitda")) / len(financials)
    score += completeness * 10

    # Bonus for interesting margin trends
    if len(financials) >= 3:
        margins = [f.get("gross_margin") for f in financials if f.get("gross_margin")]
        if margins:
            volatility = max(margins) - min(margins)
            if volatility > 0.1:
                score += 10

    return min(100, max(0, score))
```