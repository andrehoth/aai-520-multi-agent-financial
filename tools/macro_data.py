# tools/macro_data.py

import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv
import os

load_dotenv()

USING_MOCK = False

# FRED series IDs for macro indicators
SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "cpi": "CPIAUCSL",
    "unemployment_rate": "UNRATE",
}


def fetch_macro_indicators(
    api_key: str = None, start_date: str = "2024-01-01", end_date: str = None
) -> dict:
    """
    Fetch macroeconomic indicators from FRED.

    Args:
        api_key: FRED API key; falls back to FRED_API_KEY env variable
        start_date: Start date for data range (default "2024-01-01")
        end_date: End date for data range (default today)

    Returns:
        Dict with keys: fed_funds_rate, cpi, unemployment_rate.
        Each value is a list of dicts with keys: date, value.
        Returns dict with empty lists on API failure rather than halting
        the pipeline.
    """
    if USING_MOCK:
        return _mock_macro_indicators()
    return _live_macro_indicators(
        api_key or os.getenv("FRED_API_KEY"), start_date, end_date
    )


def _live_macro_indicators(api_key: str, start_date: str, end_date: str) -> dict:
    """
    Returns dict with empty lists per indicator on failure rather than
    halting the pipeline. Individual series failures do not block other
    series from being fetched.
    """
    try:
        fred = Fred(api_key=api_key)
        result = {}
        for name, series_id in SERIES.items():
            try:
                data = fred.get_series(
                    series_id, observation_start=start_date, observation_end=end_date
                )
                result[name] = [
                    {"date": str(date.date()), "value": round(float(value), 4)}
                    for date, value in data.items()
                    if pd.notna(value)
                ]
            except Exception as e:
                print(f"      Warning: FRED series {series_id} fetch failed -- {e}")
                result[name] = []
        return result
    except Exception as e:
        print(f"      Warning: macro indicators fetch failed -- {e}")
        return {name: [] for name in SERIES}


def _mock_macro_indicators() -> dict:
    return {
        "fed_funds_rate": [{"date": "2026-08-01", "value": 4.33}],
        "cpi": [{"date": "2026-08-01", "value": 314.5}],
        "unemployment_rate": [{"date": "2026-08-01", "value": 4.2}],
    }
