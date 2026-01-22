from datetime import datetime, timedelta
from typing import Optional


def generate_snapshots(
    stock_id: int,
    prices: list[dict],
    min_history_years: int = 5,
    forward_months: int = 24,
    min_snapshot_year: int = 2023
) -> list[dict]:
    """
    Generate valid snapshot dates for a stock.
    Returns list of snapshot records with computed outcomes.

    min_snapshot_year: Only create snapshots from this year onwards.
    This ensures we have valid historical financial data (yfinance only provides ~4 years).
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

    # Enforce minimum snapshot year to ensure valid financial data
    min_date = datetime(min_snapshot_year, 1, 1).date()
    if isinstance(earliest, datetime):
        earliest = earliest.date()
    if isinstance(latest, datetime):
        latest = latest.date()
    if earliest < min_date:
        earliest = min_date

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

    # Convert snapshot_date to date if it's a datetime
    if isinstance(snapshot_date, datetime):
        snapshot_date_obj = snapshot_date.date()
    else:
        snapshot_date_obj = snapshot_date

    def get_price(target_date) -> Optional[float]:
        """Find the first price on or after target date."""
        if isinstance(target_date, datetime):
            target = target_date.date()
        else:
            target = target_date
        for p in prices:
            if p["date"] >= target:
                return p["adj_close"]
        return None

    t0_price = get_price(snapshot_date_obj)
    t6_price = get_price(snapshot_date_obj + timedelta(days=182))
    t12_price = get_price(snapshot_date_obj + timedelta(days=365))
    t24_price = get_price(snapshot_date_obj + timedelta(days=forward_months * 30))

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
    """
    Classify the 24-month return as value, trap, or neutral.

    - Value: >= 30% gain (good investment)
    - Trap: <= -20% loss (bad investment)
    - Neutral: In between (not used in game)
    """
    if return_24mo >= 0.30:
        return "value"
    elif return_24mo <= -0.20:
        return "trap"
    return "neutral"


def classify_difficulty(return_24mo: float) -> str:
    """
    Classify how obvious the outcome is.

    - Easy: Extreme returns (>= 50%), obvious in hindsight
    - Hard: Close calls (<= 10%), could go either way
    - Medium: In between
    """
    abs_return = abs(return_24mo)
    if abs_return >= 0.50:
        return "easy"  # Obvious outcomes
    elif abs_return <= 0.10:
        return "hard"  # Close calls
    return "medium"
