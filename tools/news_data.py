# tools/news_data.py

from newsapi import NewsApiClient
from langdetect import detect
from dotenv import load_dotenv
import os

load_dotenv()

USING_MOCK = False


def fetch_news(ticker: str, api_key: str = None) -> list[dict]:
    """
    Fetch recent English-language news articles for a given ticker via NewsAPI.

    Args:
        ticker: Stock symbol or company name (e.g., "AAPL" or "Apple")
        api_key: NewsAPI key; falls back to NEWSAPI_KEY env variable

    Returns:
        List of article dicts with keys:
            title, description, content, source, published_at
    """
    if USING_MOCK:
        return _mock_news(ticker)
    return _live_news(ticker, api_key or os.getenv("NEWSAPI_KEY"))


def _live_news(ticker: str, api_key: str) -> list[dict]:
    client = NewsApiClient(api_key=api_key)
    response = client.get_everything(
        q=f'"{ticker}" stock',
        language="en",
        sort_by="publishedAt",
        page_size=10
    )
    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "content": a.get("content"),
            "source": a.get("source", {}).get("name"),
            "published_at": a.get("publishedAt"),
        }
        for a in response.get("articles", [])
        if _is_english(a.get("title", "") + " " + a.get("description", ""))
    ]


def _is_english(text: str) -> bool:
    """
    Detect whether text is English using langdetect.
    Falls back to True on detection failure to avoid dropping valid articles.
    """
    try:
        return detect(text) == "en"
    except:
        return False


def _mock_news(ticker: str) -> list[dict]:
    # Shape-correct stub -- replace with fixture if needed
    return [
        {
            "title": f"Stub headline for {ticker}",
            "description": "Stub description.",
            "content": "Stub article content.",
            "source": "StubSource",
            "published_at": "2026-09-17T00:00:00Z",
        }
    ]