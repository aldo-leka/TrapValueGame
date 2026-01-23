import pandas as pd
import requests
from io import StringIO


def fetch_sp500_tickers() -> list[str]:
    """Fetch current S&P 500 tickers from Wikipedia.

    Returns list of ticker symbols formatted for yfinance (e.g., BRK.B → BRK-B).
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    # Wikipedia blocks requests without a proper User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    df = tables[0]  # First table has current constituents

    # Convert tickers: BRK.B → BRK-B for yfinance compatibility
    tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()

    return tickers


# Fallback list in case Wikipedia is unavailable
FALLBACK_SP500_SAMPLE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "UNH", "JNJ", "JPM", "V", "PG", "XOM", "HD", "CVX", "MA", "ABBV",
    "MRK", "LLY", "PEP", "KO", "COST", "AVGO", "TMO", "WMT", "MCD",
    "CSCO", "ACN", "ABT", "DHR", "VZ", "NEE", "ADBE", "CMCSA", "TXN",
    "PM", "NKE", "WFC", "BMY", "UPS", "RTX", "ORCL", "HON", "QCOM",
    "COP", "LOW", "SPGI", "MS", "BA"
]
