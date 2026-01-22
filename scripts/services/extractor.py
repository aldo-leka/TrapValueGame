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

        total_assets = get(balance, "Total Assets")
        total_debt = get(balance, "Total Debt", "Long Term Debt")
        cash = get(balance, "Cash And Cash Equivalents", "Cash")
        total_equity = get(balance, "Total Equity Gross Minority Interest", "Stockholders Equity")
        shares = get(balance, "Ordinary Shares Number", "Share Issued")

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
            "total_assets": total_assets / self.MILLION if total_assets else None,
            "total_debt": total_debt / self.MILLION if total_debt else None,
            "cash_and_equivalents": cash / self.MILLION if cash else None,
            "total_equity": total_equity / self.MILLION if total_equity else None,
            "shares_outstanding": shares / self.MILLION if shares else None,
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
