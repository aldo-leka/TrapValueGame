# Stock Selection: Curation Criteria & Initial Dataset

This document defines which stocks to include in the game, how to curate interesting scenarios, and provides an initial seed list.

---

## Table of Contents
1. [Selection Philosophy](#selection-philosophy)
2. [Technical Requirements](#technical-requirements)
3. [Educational Value Criteria](#educational-value-criteria)
4. [Scenario Categories](#scenario-categories)
5. [Initial Stock List](#initial-stock-list)
6. [Exclusion Criteria](#exclusion-criteria)
7. [Maintenance & Updates](#maintenance--updates)

---

## Selection Philosophy

The game should teach value investing principles through **memorable, educational scenarios**. The best stocks for the game are:

1. **Recognizable** - Players should have an "aha!" moment when revealed
2. **Dramatic** - Clear outcomes (big winners or big losers, not flat)
3. **Instructive** - The financials tell a story that supports the outcome
4. **Diverse** - Cover multiple sectors, time periods, and scenario types

### What Makes a Good Scenario?

| Good Scenario | Bad Scenario |
|---------------|--------------|
| Tesla 2019: "Is EV hype justified?" | Random small-cap nobody knows |
| Netflix 2011: "Can streaming beat DVDs?" | Stock that moved +5% in 2 years |
| Enron 2000: "Too good to be true?" | Company with incomplete financials |
| GameStop 2018: "Dying retailer?" | Merger arbitrage situations |

---

## Technical Requirements

### Minimum Data Requirements

For a stock to be included, it must have:

| Requirement | Threshold | Reason |
|-------------|-----------|--------|
| **Price History** | 7+ years | 5 years before + 2 years after |
| **Financial Statements** | 5+ annual reports | Full analysis window |
| **Required Metrics** | Revenue, Net Income | Core analysis metrics |
| **Trading Status** | Listed (current or historical) | yfinance accessibility |

### Data Quality Checks

```python
def validate_stock_for_game(ticker: str) -> tuple[bool, list[str]]:
    """
    Validate a stock meets minimum requirements.
    Returns (is_valid, list_of_issues)
    """
    issues = []

    extractor = YFinanceExtractor()

    # Check company info
    info = extractor.fetch_company_info(ticker)
    if not info["company_name"]:
        issues.append("Company name not found")

    if not info["sector"]:
        issues.append("Sector not available")

    # Check financial history
    financials = extractor.fetch_financials(ticker, datetime.now())

    if len(financials) < 5:
        issues.append(f"Only {len(financials)} years of financials (need 5+)")

    # Check for required fields
    missing_revenue = sum(1 for f in financials if not f.get("revenue"))
    if missing_revenue > 1:
        issues.append(f"Missing revenue for {missing_revenue} years")

    missing_income = sum(1 for f in financials if f.get("net_income") is None)
    if missing_income > 2:
        issues.append(f"Missing net income for {missing_income} years")

    # Check price history
    prices = extractor.fetch_prices(
        ticker,
        datetime(2010, 1, 1),
        datetime.now()
    )

    if len(prices) < 1500:  # ~6 years of trading days
        issues.append(f"Only {len(prices)} price points (need 1500+)")

    # Check for valid snapshot dates
    snapshots = generate_snapshots(1, prices)
    if len(snapshots) < 3:
        issues.append(f"Only {len(snapshots)} valid snapshots")

    return len(issues) == 0, issues
```

---

## Educational Value Criteria

### Scenario Quality Score

Each potential scenario is scored on educational value:

```python
def score_scenario_educational_value(snapshot: dict, financials: list) -> float:
    """
    Score 0-100 for how educational/interesting a scenario is.
    """
    score = 50.0  # Base score

    # === Outcome Clarity (±25 points) ===
    return_24mo = snapshot["return_24mo"]

    if abs(return_24mo) >= 0.50:
        score += 20  # Very clear outcome
    elif abs(return_24mo) >= 0.30:
        score += 10  # Clear outcome
    elif abs(return_24mo) <= 0.10:
        score -= 15  # Boring/ambiguous

    # === Financial Story (±20 points) ===
    # Does the data tell a coherent story?

    revenues = [f["revenue"] for f in financials if f.get("revenue")]
    if len(revenues) >= 3:
        # Revenue trend
        if revenues[-1] > revenues[0] * 1.5:
            score += 10  # Strong growth story
        elif revenues[-1] < revenues[0] * 0.7:
            score += 10  # Clear decline story

    net_incomes = [f["net_income"] for f in financials if f.get("net_income") is not None]
    if len(net_incomes) >= 3:
        # Profit trajectory
        positive_count = sum(1 for n in net_incomes if n > 0)
        if positive_count <= 1:
            score += 5  # Persistent losses - interesting
        elif positive_count == len(net_incomes):
            score += 5  # Consistent profits - interesting

    # === Counterintuitive Outcomes (±15 points) ===
    # Most educational scenarios defy easy assumptions

    last_year_income = net_incomes[-1] if net_incomes else 0
    last_year_revenue_trend = (
        (revenues[-1] - revenues[-2]) / revenues[-2]
        if len(revenues) >= 2 else 0
    )

    # Trap that looked good
    if snapshot["outcome_label"] == "trap":
        if last_year_income > 0 and last_year_revenue_trend > 0:
            score += 15  # "But everything looked fine!"

    # Value that looked bad
    if snapshot["outcome_label"] == "value":
        if last_year_income < 0 or last_year_revenue_trend < -0.1:
            score += 15  # "How did this recover?"

    # === Data Completeness (±10 points) ===
    metrics = ["revenue", "gross_margin", "ebitda", "net_income", "free_cash_flow", "total_debt"]
    completeness = sum(
        sum(1 for f in financials if f.get(m) is not None)
        for m in metrics
    ) / (len(metrics) * len(financials))

    score += completeness * 10

    return min(100, max(0, score))
```

### Minimum Educational Value Threshold

Only include scenarios with educational score >= 55

---

## Scenario Categories

### Category Distribution Target

| Category | Target % | Example Scenarios |
|----------|----------|-------------------|
| **Tech Turnarounds** | 15% | AAPL 2003, NVDA 2015, AMD 2017 |
| **Tech Traps** | 15% | CSCO 2000, INTC 2018, PYPL 2021 |
| **Retail Battles** | 15% | AMZN 2014, WMT 2015, GME 2018 |
| **Financial Crises** | 10% | BAC 2011, GS 2016, WFC 2018 |
| **Healthcare Bets** | 10% | MRNA 2019, GILD 2015, BIIB 2020 |
| **Energy Cycles** | 10% | XOM 2020, CVX 2016, OXY 2019 |
| **Consumer Brands** | 10% | NKE 2017, SBUX 2018, DIS 2019 |
| **Industrial Plays** | 10% | BA 2019, CAT 2016, DE 2020 |
| **Wildcards** | 5% | Unusual/unique situations |

### Difficulty Distribution

| Difficulty | Target % | Description |
|------------|----------|-------------|
| **Easy** | 30% | Obvious in hindsight (50%+ returns or losses) |
| **Medium** | 50% | Requires analysis (20-50% returns) |
| **Hard** | 20% | Could go either way (10-20% returns) |

---

## Initial Stock List

### Tier 1: Must-Have Iconic Scenarios (30 stocks)

These are well-known companies with memorable historical moments:

```python
TIER_1_STOCKS = [
    # Tech Giants at Crossroads
    ("AAPL", "2013-01-01"),   # Post-Jobs era doubts
    ("MSFT", "2014-01-01"),   # Pre-Nadella turnaround
    ("GOOG", "2015-01-01"),   # Alphabet restructure
    ("META", "2018-01-01"),   # Cambridge Analytica
    ("AMZN", "2014-01-01"),   # "Amazon never profits"
    ("NVDA", "2016-01-01"),   # Pre-AI boom
    ("TSLA", "2019-01-01"),   # Production hell
    ("NFLX", "2011-01-01"),   # Qwikster disaster

    # Fallen Angels
    ("INTC", "2018-01-01"),   # AMD competition
    ("IBM", "2014-01-01"),    # Cloud transition failure
    ("CSCO", "2010-01-01"),   # Post-bubble recovery
    ("PYPL", "2021-07-01"),   # Growth slowdown

    # Retail Wars
    ("GME", "2018-01-01"),    # Pre-meme stock
    ("WMT", "2015-01-01"),    # Amazon threat
    ("TGT", "2017-01-01"),    # Turnaround story
    ("BBY", "2012-01-01"),    # "Showrooming" threat

    # Finance & Banks
    ("BAC", "2011-07-01"),    # Post-crisis recovery
    ("GS", "2016-01-01"),     # Trading slump
    ("WFC", "2018-01-01"),    # Scandal aftermath
    ("JPM", "2012-01-01"),    # London Whale

    # Healthcare
    ("MRNA", "2019-07-01"),   # Pre-COVID
    ("PFE", "2019-01-01"),    # Pre-vaccine
    ("JNJ", "2018-01-01"),    # Talc lawsuits
    ("GILD", "2015-07-01"),   # Hep C peak

    # Energy
    ("XOM", "2020-01-01"),    # Pre-crash
    ("CVX", "2016-01-01"),    # Oil recovery
    ("OXY", "2019-07-01"),    # Anadarko acquisition

    # Consumer
    ("NKE", "2017-07-01"),    # DTC transition
    ("DIS", "2019-01-01"),    # Streaming launch
    ("SBUX", "2018-07-01"),   # China expansion
]
```

### Tier 2: Sector Diversification (40 stocks)

Additional stocks to fill sector gaps:

```python
TIER_2_STOCKS = [
    # More Tech
    "CRM", "ADBE", "ORCL", "SAP", "NOW", "SNOW", "PLTR",
    "UBER", "LYFT", "SQ", "SHOP", "TWLO", "ZM", "DOCU",

    # Industrials
    "BA", "CAT", "DE", "HON", "MMM", "UNP", "UPS", "FDX",

    # Consumer
    "MCD", "KO", "PEP", "PG", "CL", "EL", "LULU", "COST",

    # Healthcare
    "UNH", "CVS", "ABBV", "BMY", "LLY", "TMO", "DHR", "ISRG",

    # Finance
    "V", "MA", "AXP", "C", "MS", "SCHW", "BLK", "BX",

    # Energy & Materials
    "SLB", "HAL", "LIN", "APD", "NEM", "FCX",

    # Real Estate & Utilities
    "AMT", "PLD", "SPG", "NEE", "DUK", "SO",
]
```

### Tier 3: Historical Gems (20 stocks)

Delisted or transformed companies with great lessons:

```python
TIER_3_HISTORICAL = [
    # These may require special handling or manual data
    "ENRON",      # Fraud case study (if data available)
    "WORLDCOM",   # Accounting fraud
    "LEHMAN",     # Financial crisis
    "BLOCKBUSTER",# Disruption story

    # Acquired companies (check yfinance availability)
    "TWTR",       # Pre-Musk
    "ATVI",       # Pre-Microsoft acquisition
    "VMW",        # Pre-Broadcom
]
```

---

## Exclusion Criteria

### Automatic Exclusions

Do NOT include stocks that:

| Exclusion Reason | Example | Why |
|------------------|---------|-----|
| **SPACs** | DWAC, LCID pre-merge | Unusual price dynamics |
| **Penny Stocks** | Price < $1 | Manipulation risk |
| **ADRs of obscure companies** | Random Chinese stocks | Recognition issue |
| **Leveraged ETFs** | TQQQ, SOXL | Not real companies |
| **REITs with complex structures** | Mortgage REITs | Too specialized |
| **Biotech with no revenue** | Pre-clinical only | Pure speculation |
| **Recent IPOs** | < 7 years public | Insufficient history |
| **Companies in active bankruptcy** | — | Data unreliable |

### Manual Review Triggers

Flag for human review if:

```python
def needs_manual_review(ticker: str, info: dict, financials: list) -> list[str]:
    """Return list of reasons for manual review, empty if OK."""
    flags = []

    # Massive one-time events
    for f in financials:
        if f.get("net_income") and f.get("revenue"):
            if abs(f["net_income"]) > f["revenue"] * 2:
                flags.append(f"Unusual net income in {f['fiscal_year']}")

    # Recent major restructuring
    if info.get("industry") != info.get("previous_industry"):
        flags.append("Industry classification changed")

    # Negative equity
    for f in financials:
        if f.get("total_equity") and f["total_equity"] < 0:
            flags.append(f"Negative equity in {f['fiscal_year']}")

    return flags
```

---

## Maintenance & Updates

### Quarterly Updates

Run every quarter to:

1. **Add New Snapshots** - Existing stocks get new valid snapshot dates
2. **Validate Existing Data** - Check for splits, restatements
3. **Update Outcomes** - Snapshots that now have 24-month data

```python
async def quarterly_update():
    """Quarterly maintenance routine."""

    db = await get_db()

    # 1. Find stocks needing new snapshots
    async with db.execute("""
        SELECT s.ticker, MAX(snap.snapshot_date) as last_snapshot
        FROM stocks s
        LEFT JOIN snapshots snap ON s.id = snap.stock_id
        WHERE s.is_active = 1
        GROUP BY s.id
        HAVING last_snapshot < date('now', '-3 months')
           OR last_snapshot IS NULL
    """) as cursor:
        stocks_to_update = await cursor.fetchall()

    # 2. Generate new snapshots for each
    for ticker, _ in stocks_to_update:
        await refresh_stock_snapshots(ticker)

    # 3. Validate existing snapshot outcomes
    await validate_all_outcomes()

    # 4. Generate narratives for snapshots missing them
    await generate_missing_narratives()

    await db.close()
```

### Annual Review

Once per year:

1. **Add new iconic scenarios** - Major events from past year
2. **Retire stale scenarios** - Remove if outcome is now well-known
3. **Rebalance categories** - Ensure diversity targets are met
4. **Update difficulty ratings** - Based on player accuracy data

### Scenario Retirement Criteria

Remove a snapshot if:

```python
def should_retire_scenario(snapshot: dict) -> bool:
    """Determine if a scenario should be retired."""

    # Too well known (players always guess correctly)
    if snapshot["times_played"] > 100:
        accuracy = snapshot["correct_guesses"] / snapshot["times_played"]
        if accuracy > 0.90:
            return True  # Too easy now

    # Too old (> 10 years ago)
    if snapshot["snapshot_date"].year < datetime.now().year - 10:
        return True

    # Outcome is now culturally famous
    FAMOUS_SCENARIOS = [
        # Add scenario IDs that have become memes/common knowledge
    ]
    if snapshot["id"] in FAMOUS_SCENARIOS:
        return True

    return False
```

---

## Seeding Commands

### Initial Database Population

```bash
# Tier 1 - Must-haves
curl -X POST http://localhost:8000/admin/seed \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": [
      "AAPL", "MSFT", "GOOG", "META", "AMZN", "NVDA", "TSLA", "NFLX",
      "INTC", "IBM", "CSCO", "PYPL", "GME", "WMT", "TGT", "BBY",
      "BAC", "GS", "WFC", "JPM", "MRNA", "PFE", "JNJ", "GILD",
      "XOM", "CVX", "OXY", "NKE", "DIS", "SBUX"
    ]
  }'

# Tier 2 - Diversification (split into batches)
curl -X POST http://localhost:8000/admin/seed \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": [
      "CRM", "ADBE", "ORCL", "SAP", "NOW", "SQ", "SHOP",
      "BA", "CAT", "DE", "HON", "MMM", "UNP", "UPS",
      "MCD", "KO", "PEP", "PG", "COST", "UNH", "CVS"
    ]
  }'
```

### Validation Script

```bash
# Check stock coverage by sector
curl http://localhost:8000/admin/stats/sectors

# Check scenario count by difficulty
curl http://localhost:8000/admin/stats/difficulty

# List stocks failing validation
curl http://localhost:8000/admin/validate
```