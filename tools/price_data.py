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
        Date-indexed DataFrame with columns: Open, High, Low, Close, Volume.
        Returns empty DataFrame on API failure rather than halting the pipeline.
    """
    return _live_price_history(ticker, period)


def fetch_price_summary(ticker: str) -> dict:
    """
    Fetch current price summary statistics for a given ticker via yfinance.

    Args:
        ticker: Stock symbol (e.g., "AAPL")

    Returns:
        Dict with keys: ticker, current_price, week_52_high, week_52_low,
        avg_volume, market_cap. Returns dict with None values on API failure
        rather than halting the pipeline.
    """
    return _live_price_summary(ticker)


def _live_price_history(ticker: str, period: str) -> pd.DataFrame:
    """
    Returns empty DataFrame on failure rather than halting the pipeline.
    """
    try:
        data = yf.Ticker(ticker).history(period=period)
        data.index = data.index.date
        data.index.name = "Date"
        return data[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        print(f"      Warning: price history fetch failed for {ticker} -- {e}")
        return pd.DataFrame()


def _live_price_summary(ticker: str) -> dict:
    """
    Returns dict with None values on failure rather than halting the pipeline.
    """
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker,
            "current_price": info.get("currentPrice"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
        }
    except Exception as e:
        print(f"      Warning: price summary fetch failed for {ticker} -- {e}")
        return {
            "ticker": ticker,
            "current_price": None,
            "week_52_high": None,
            "week_52_low": None,
            "avg_volume": None,
            "market_cap": None,
        }
