from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class FinancialYear(BaseModel):
    fiscal_year: int
    revenue: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None


class GameSnapshot(BaseModel):
    snapshot_id: int
    fake_name: str
    sector: str
    industry: Optional[str] = None
    snapshot_date: date
    snapshot_year: int
    financials: list[FinancialYear]
    narrative: Optional[str] = None


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
    error: Optional[str] = None
