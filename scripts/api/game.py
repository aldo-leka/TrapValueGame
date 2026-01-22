from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models.schemas import GameSnapshot, RevealResponse, FinancialYear, PricePoint
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

    try:
        # Build query with filters
        query = """
            SELECT s.id, s.snapshot_date, s.narrative, s.stock_id,
                   st.fake_name, st.sector, st.industry
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

        snapshot_id, snapshot_date, narrative, stock_id, fake_name, sector_val, industry = row

        # Get financials for this snapshot
        financials = await get_financials_for_snapshot(db, stock_id, snapshot_date)

        # Parse the snapshot_year from snapshot_date
        # snapshot_date could be a string or date object
        if isinstance(snapshot_date, str):
            snapshot_year = int(snapshot_date.split("-")[0])
        else:
            snapshot_year = snapshot_date.year

        return GameSnapshot(
            snapshot_id=snapshot_id,
            fake_name=fake_name,
            sector=sector_val or "Unknown",
            industry=industry,
            snapshot_date=snapshot_date,
            snapshot_year=snapshot_year,
            financials=financials,
            narrative=narrative
        )
    finally:
        await db.close()


@router.post("/reveal/{snapshot_id}", response_model=RevealResponse)
async def reveal_outcome(snapshot_id: int, player_choice: str):
    """Reveal the outcome for a snapshot."""
    if player_choice not in ("value", "trap"):
        raise HTTPException(400, "Choice must be 'value' or 'trap'")

    db = await get_db()

    try:
        # Get snapshot and stock data
        query = """
            SELECT s.id, s.stock_id, s.snapshot_date, s.price_at_snapshot,
                   s.price_at_24mo, s.return_24mo, s.outcome_label,
                   st.ticker, st.company_name
            FROM snapshots s
            JOIN stocks st ON s.stock_id = st.id
            WHERE s.id = ?
        """
        async with db.execute(query, [snapshot_id]) as cursor:
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(404, "Snapshot not found")

        (s_id, stock_id, snapshot_date, price_at_snapshot, price_at_24mo,
         return_24mo, outcome_label, ticker, company_name) = row

        # Get price series for chart
        price_query = """
            SELECT date, adj_close
            FROM price_history
            WHERE stock_id = ?
              AND date >= ?
              AND date <= date(?, '+24 months')
            ORDER BY date
        """
        async with db.execute(price_query, [stock_id, snapshot_date, snapshot_date]) as cursor:
            price_rows = await cursor.fetchall()

        # Determine if correct
        is_correct = (
            (player_choice == "value" and outcome_label == "value") or
            (player_choice == "trap" and outcome_label == "trap")
        )

        # Update play stats
        await db.execute("""
            UPDATE snapshots
            SET times_played = times_played + 1,
                correct_guesses = correct_guesses + ?
            WHERE id = ?
        """, [1 if is_correct else 0, snapshot_id])
        await db.commit()

        return RevealResponse(
            ticker=ticker,
            company_name=company_name,
            snapshot_date=snapshot_date,
            price_at_snapshot=price_at_snapshot,
            price_at_24mo=price_at_24mo,
            return_24mo=return_24mo,
            outcome_label=outcome_label,
            player_choice=player_choice,
            is_correct=is_correct,
            price_series=[
                PricePoint(date=row[0], price=row[1])
                for row in price_rows
            ]
        )
    finally:
        await db.close()


async def get_financials_for_snapshot(db, stock_id: int, snapshot_date) -> list[FinancialYear]:
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

    # Return in chronological order (oldest first)
    return [
        FinancialYear(
            fiscal_year=row[0],
            revenue=row[1],
            gross_margin=row[2],
            operating_income=row[3],
            ebitda=row[4],
            net_income=row[5],
            free_cash_flow=row[6],
            total_debt=row[7],
            cash_and_equivalents=row[8],
        )
        for row in reversed(rows)
    ]
