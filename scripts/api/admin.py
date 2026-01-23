import asyncio
from fastapi import APIRouter, BackgroundTasks
from models.schemas import SeedRequest, SeedResult
from services.extractor import YFinanceExtractor
from services.snapshot_generator import generate_snapshots
from services.fake_names import generate_fake_name
from services.stock_list import fetch_sp500_tickers, FALLBACK_SP500_SAMPLE
from services.database import get_db
from datetime import datetime

router = APIRouter()

# Progress tracking for long-running seed jobs
_seed_progress = {
    "status": "idle",
    "total": 0,
    "processed": 0,
    "successful": 0,
    "failed": 0,
    "current_ticker": None,
    "started_at": None,
    "errors": []
}


@router.post("/seed")
async def seed_database(request: SeedRequest, background_tasks: BackgroundTasks):
    """Seed database with stock data. Runs in background."""
    background_tasks.add_task(seed_tickers_with_rate_limit, request.tickers, request.force_refresh)
    return {"message": f"Seeding {len(request.tickers)} tickers in background"}


@router.post("/seed-sp500")
async def seed_sp500(background_tasks: BackgroundTasks, force_refresh: bool = False):
    """Seed all S&P 500 companies. Runs in background with rate limiting."""
    try:
        tickers = fetch_sp500_tickers()
    except Exception as e:
        print(f"Failed to fetch S&P 500 list: {e}, using fallback")
        tickers = FALLBACK_SP500_SAMPLE

    background_tasks.add_task(seed_tickers_with_rate_limit, tickers, force_refresh)
    return {"message": f"Seeding {len(tickers)} S&P 500 tickers in background"}


@router.get("/status")
async def get_seed_status():
    """Get current database status."""
    db = await get_db()
    try:
        async with db.execute("SELECT COUNT(*) FROM stocks") as cursor:
            stocks = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM snapshots") as cursor:
            snapshots = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM snapshots WHERE outcome_label IN ('value', 'trap')") as cursor:
            playable = (await cursor.fetchone())[0]
        return {
            "stocks": stocks,
            "snapshots": snapshots,
            "playable_snapshots": playable
        }
    finally:
        await db.close()


@router.get("/seed-progress")
async def get_seed_progress():
    """Get progress of current seeding job."""
    return _seed_progress


async def seed_tickers_with_rate_limit(
    tickers: list[str],
    force_refresh: bool,
    delay_seconds: float = 2.0,
    batch_size: int = 10
):
    """Background task to seed ticker data with rate limiting and batch commits."""
    global _seed_progress

    # Reset progress
    _seed_progress = {
        "status": "running",
        "total": len(tickers),
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "current_ticker": None,
        "started_at": datetime.now().isoformat(),
        "errors": []
    }

    extractor = YFinanceExtractor()
    db = await get_db()

    try:
        # Get existing fake names to avoid duplicates
        async with db.execute("SELECT fake_name FROM stocks") as cursor:
            used_names = {row[0] for row in await cursor.fetchall()}

        for i, ticker in enumerate(tickers):
            _seed_progress["current_ticker"] = ticker

            try:
                result = await seed_single_ticker(
                    db, extractor, ticker, used_names, force_refresh
                )

                if result["success"]:
                    _seed_progress["successful"] += 1
                    used_names.add(result.get("fake_name", ""))
                else:
                    _seed_progress["failed"] += 1
                    if result.get("error"):
                        _seed_progress["errors"].append({
                            "ticker": ticker,
                            "error": result["error"]
                        })

                print(f"[{i+1}/{len(tickers)}] {ticker}: {result}")

            except Exception as e:
                _seed_progress["failed"] += 1
                _seed_progress["errors"].append({
                    "ticker": ticker,
                    "error": str(e)
                })
                print(f"[{i+1}/{len(tickers)}] Error seeding {ticker}: {e}")

            _seed_progress["processed"] += 1

            # Batch commit every N stocks
            if (i + 1) % batch_size == 0:
                await db.commit()
                print(f"Committed batch at {i + 1} stocks")

            # Rate limiting delay (skip for last ticker)
            if i < len(tickers) - 1:
                await asyncio.sleep(delay_seconds)

        # Final commit
        await db.commit()

        _seed_progress["status"] = "completed"
        _seed_progress["current_ticker"] = None
        print(f"Seeding completed: {_seed_progress['successful']} successful, {_seed_progress['failed']} failed")

    except Exception as e:
        _seed_progress["status"] = "error"
        _seed_progress["errors"].append({"ticker": "GLOBAL", "error": str(e)})
        print(f"Seeding failed with error: {e}")
    finally:
        await db.close()


# Keep original function for backwards compatibility
async def seed_tickers(tickers: list[str], force_refresh: bool):
    """Legacy seeding without rate limiting. Use seed_tickers_with_rate_limit for bulk."""
    await seed_tickers_with_rate_limit(tickers, force_refresh, delay_seconds=0.5, batch_size=5)


async def seed_single_ticker(db, extractor, ticker: str, used_names: set, force: bool) -> dict:
    """Seed a single ticker's data."""

    # Check if exists
    async with db.execute(
        "SELECT id FROM stocks WHERE ticker = ?", [ticker.upper()]
    ) as cursor:
        existing = await cursor.fetchone()

    if existing and not force:
        return {
            "ticker": ticker,
            "success": True,
            "snapshots_created": 0,
            "note": "Already exists"
        }

    # Fetch company info
    info = extractor.fetch_company_info(ticker)
    if not info["company_name"] or info["company_name"] == "Unknown":
        return {"ticker": ticker, "success": False, "snapshots_created": 0, "error": "Company not found"}

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
    """, [ticker.upper(), info["company_name"], fake_name, info["sector"], info["industry"], info["market_cap_tier"]])

    # Get stock ID
    async with db.execute("SELECT id FROM stocks WHERE ticker = ?", [ticker.upper()]) as cursor:
        stock_id = (await cursor.fetchone())[0]

    # Fetch price history (10 years)
    now = datetime.now()
    prices = extractor.fetch_prices(
        ticker,
        datetime(now.year - 10, 1, 1),
        now
    )

    if not prices:
        return {"ticker": ticker, "success": False, "snapshots_created": 0, "error": "No price history found"}

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
                operating_margin, net_margin, total_assets, total_debt,
                cash_and_equivalents, total_equity, operating_cash_flow,
                capital_expenditures, free_cash_flow, shares_outstanding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            stock_id, f["fiscal_year"], f["report_date"], f.get("revenue"),
            f.get("gross_profit"), f.get("operating_income"), f.get("ebitda"),
            f.get("net_income"), f.get("gross_margin"), f.get("operating_margin"),
            f.get("net_margin"), f.get("total_assets"), f.get("total_debt"),
            f.get("cash_and_equivalents"), f.get("total_equity"),
            f.get("operating_cash_flow"), f.get("capital_expenditures"),
            f.get("free_cash_flow"), f.get("shares_outstanding")
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

    # Count playable snapshots (value or trap only)
    playable = len([s for s in snapshots if s["outcome_label"] in ("value", "trap")])

    return {
        "ticker": ticker,
        "success": True,
        "snapshots_created": len(snapshots),
        "playable_snapshots": playable,
        "fake_name": fake_name
    }
