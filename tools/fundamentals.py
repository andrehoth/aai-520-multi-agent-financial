# tools/fundamentals.py


import requests
from dotenv import load_dotenv
import os

load_dotenv()

USING_MOCK = False


def fetch_earnings(ticker: str, api_key: str = None, quarters: int = 8) -> list[dict]:
    """
    Fetch recent quarterly earnings for a given ticker via Alpha Vantage.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        api_key: Alpha Vantage key; falls back to ALPHA_VANTAGE_KEY env variable
        quarters: Number of most recent quarters to return (default 8)

    Returns:
        List of dicts with keys:
            fiscalDateEnding, reportedDate, reportedEPS, estimatedEPS,
            surprise, surprisePercentage, reportTime.
        Returns empty list on API failure rather than halting the pipeline.
    """
    if USING_MOCK:
        return _mock_earnings(ticker)
    return _live_earnings(ticker, api_key or os.getenv("ALPHA_VANTAGE_KEY"), quarters)


def fetch_income_statement(
    ticker: str, api_key: str = None, quarters: int = 8
) -> list[dict]:
    """
    Fetch recent quarterly income statements for a given ticker via Alpha Vantage.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        api_key: Alpha Vantage key; falls back to ALPHA_VANTAGE_KEY env variable
        quarters: Number of most recent quarters to return (default 8)

    Returns:
        List of dicts with keys:
            fiscalDateEnding, totalRevenue, grossProfit, operatingIncome, netIncome.
        Returns empty list on API failure rather than halting the pipeline.
    """
    if USING_MOCK:
        return _mock_income_statement(ticker)
    return _live_income_statement(
        ticker, api_key or os.getenv("ALPHA_VANTAGE_KEY"), quarters
    )


def _live_earnings(ticker: str, api_key: str, quarters: int) -> list[dict]:
    """
    Returns empty list on failure rather than halting the pipeline.
    """
    try:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=EARNINGS&symbol={ticker}&apikey={api_key}"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("quarterlyEarnings", [])[:quarters]
    except Exception as e:
        print(f"      Warning: earnings fetch failed for {ticker} -- {e}")
        return []


def _live_income_statement(ticker: str, api_key: str, quarters: int) -> list[dict]:
    """
    Returns empty list on failure rather than halting the pipeline.
    """
    try:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        quarterly = data.get("quarterlyReports", [])[:quarters]
        return [
            {
                "fiscalDateEnding": r.get("fiscalDateEnding"),
                "totalRevenue": r.get("totalRevenue"),
                "grossProfit": r.get("grossProfit"),
                "operatingIncome": r.get("operatingIncome"),
                "netIncome": r.get("netIncome"),
            }
            for r in quarterly
        ]
    except Exception as e:
        print(f"      Warning: income statement fetch failed for {ticker} -- {e}")
        return []


def _mock_earnings(ticker: str) -> list[dict]:
    return [
        {
            "fiscalDateEnding": "2026-06-30",
            "reportedDate": "2026-07-30",
            "reportedEPS": "2.02",
            "estimatedEPS": "1.88",
            "surprise": "0.14",
            "surprisePercentage": "7.4468",
            "reportTime": "post-market",
        }
    ]


def _mock_income_statement(ticker: str) -> list[dict]:
    return [
        {
            "fiscalDateEnding": "2026-06-30",
            "totalRevenue": "94000000000",
            "grossProfit": "43000000000",
            "operatingIncome": "29000000000",
            "netIncome": "25000000000",
        }
    ]
