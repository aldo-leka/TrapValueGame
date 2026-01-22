import aiosqlite
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "./shared/stocks.db")


async def init_db():
    """Initialize database with schema."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)

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
        print("Database initialized successfully")


async def get_db():
    """Get database connection."""
    return await aiosqlite.connect(DATABASE_PATH)
