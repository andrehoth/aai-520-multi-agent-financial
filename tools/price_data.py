# tools/price_data.py

import yfinance as yf
import pandas as pd

USING_MOCK = False


def fetch_price_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    Fetch OHLCV price history for a given ticker via yfinance.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        period: Lookback period (e.g., "1mo", "3mo", "1y")

    Returns:
        Date-indexed DataFrame with columns: Open, High, Low, Close, Volume
    """
    return _live_price_history(ticker, period)


def fetch_price_summary(ticker: str) -> dict:
    """
    Fetch current price summary statistics for a given ticker via yfinance.

    Args:
        ticker: Stock symbol (e.g., "AAPL")

    Returns:
        Dict with keys: ticker, current_price, week_52_high, week_52_low,
        avg_volume, market_cap
    """
    return _live_price_summary(ticker)


def _live_price_history(ticker: str, period: str) -> pd.DataFrame:
    data = yf.Ticker(ticker).history(period=period)
    return data[["Open", "High", "Low", "Close", "Volume"]]


def _live_price_summary(ticker: str) -> dict:
    info = yf.Ticker(ticker).info
    return {
        "ticker": ticker,
        "current_price": info.get("currentPrice"),
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "market_cap": info.get("marketCap"),
    }