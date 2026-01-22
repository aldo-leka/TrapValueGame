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


async def seed_tickers(tickers: list[str], force_refresh: bool):
    """Background task to seed ticker data."""
    extractor = YFinanceExtractor()
    db = await get_db()

    try:
        # Get existing fake names to avoid duplicates
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
                print(f"Seeded {ticker}: {result}")
            except Exception as e:
                results.append({
                    "ticker": ticker,
                    "success": False,
                    "snapshots_created": 0,
                    "error": str(e)
                })
                print(f"Error seeding {ticker}: {e}")

        return results
    finally:
        await db.close()


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

    await db.commit()

    # Count playable snapshots (value or trap only)
    playable = len([s for s in snapshots if s["outcome_label"] in ("value", "trap")])

    return {
        "ticker": ticker,
        "success": True,
        "snapshots_created": len(snapshots),
        "playable_snapshots": playable,
        "fake_name": fake_name
    }
