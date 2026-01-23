"""Shared fixtures and configuration for tests."""

import pytest
import sys
from pathlib import Path
from datetime import date, timedelta

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        "ticker": "TEST",
        "company_name": "Test Corporation",
        "sector": "Technology",
        "industry": "Software",
        "market_cap_tier": "large",
    }


@pytest.fixture
def sample_price_series():
    """Generate a sample price series for testing."""
    base_date = date(2018, 1, 1)
    base_price = 100.0

    prices = []
    for i in range(2000):  # ~5.5 years
        # Add some volatility
        import random
        random.seed(i)  # Deterministic for testing
        daily_change = random.uniform(-0.02, 0.025)

        if i == 0:
            price = base_price
        else:
            price = prices[-1]["adj_close"] * (1 + daily_change)

        prices.append({
            "date": base_date + timedelta(days=i),
            "adj_close": round(price, 2),
            "volume": random.randint(1000000, 10000000),
        })

    return prices


@pytest.fixture
def value_stock_prices():
    """Generate price data that results in a 'value' classification (>= 30% gain)."""
    base_date = date(2020, 1, 1)
    prices = []

    # Start at $100, end at $140+ after 24 months
    for i in range(800):  # ~2.2 years
        price = 100 + (i * 0.06)  # Steady growth
        prices.append({
            "date": base_date + timedelta(days=i),
            "adj_close": round(price, 2),
        })

    return prices


@pytest.fixture
def trap_stock_prices():
    """Generate price data that results in a 'trap' classification (<= -20% loss)."""
    base_date = date(2020, 1, 1)
    prices = []

    # Start at $100, end at $75 or less after 24 months
    for i in range(800):
        price = max(100 - (i * 0.04), 50)  # Steady decline
        prices.append({
            "date": base_date + timedelta(days=i),
            "adj_close": round(price, 2),
        })

    return prices


@pytest.fixture
def neutral_stock_prices():
    """Generate price data that results in a 'neutral' classification."""
    base_date = date(2020, 1, 1)
    prices = []

    # Start at $100, end around $110 after 24 months (10% gain - neutral)
    for i in range(800):
        price = 100 + (i * 0.015)  # Very slow growth
        prices.append({
            "date": base_date + timedelta(days=i),
            "adj_close": round(price, 2),
        })

    return prices


@pytest.fixture
def sample_financials():
    """Sample financial data for testing."""
    return [
        {
            "fiscal_year": 2020,
            "report_date": date(2021, 3, 15),
            "revenue": 10000.0,
            "gross_profit": 6000.0,
            "operating_income": 2500.0,
            "net_income": 1800.0,
            "free_cash_flow": 2000.0,
        },
        {
            "fiscal_year": 2021,
            "report_date": date(2022, 3, 15),
            "revenue": 12000.0,
            "gross_profit": 7200.0,
            "operating_income": 3000.0,
            "net_income": 2200.0,
            "free_cash_flow": 2500.0,
        },
        {
            "fiscal_year": 2022,
            "report_date": date(2023, 3, 15),
            "revenue": 15000.0,
            "gross_profit": 9000.0,
            "operating_income": 4000.0,
            "net_income": 3000.0,
            "free_cash_flow": 3200.0,
        },
    ]


@pytest.fixture
def mock_db_connection(tmp_path):
    """Create a temporary database for testing."""
    import sqlite3

    db_path = tmp_path / "test_stocks.db"
    conn = sqlite3.connect(str(db_path))

    # Create minimal schema
    conn.executescript("""
        CREATE TABLE stocks (
            id INTEGER PRIMARY KEY,
            ticker TEXT UNIQUE,
            company_name TEXT,
            fake_name TEXT,
            sector TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE financials (
            id INTEGER PRIMARY KEY,
            stock_id INTEGER,
            fiscal_year INTEGER,
            revenue REAL
        );

        CREATE TABLE snapshots (
            id INTEGER PRIMARY KEY,
            stock_id INTEGER,
            snapshot_date TEXT,
            price_at_snapshot REAL,
            price_at_24mo REAL,
            return_24mo REAL,
            outcome_label TEXT,
            difficulty TEXT
        );
    """)

    conn.commit()

    yield conn, str(db_path)

    conn.close()
