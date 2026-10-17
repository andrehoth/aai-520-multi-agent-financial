# tests/test_news_data.py
"""
Contract tests for the fetch_news tool defined in tools/news_data.py.

Validates error handling behavior without making live API calls.
Run with:

    python -m pytest tests/test_news_data.py -v
"""

from unittest.mock import patch, MagicMock


def test_fetch_news_returns_empty_list_on_api_failure():
    """fetch_news should return an empty list on API failure rather than
    raising an exception and halting the pipeline."""
    with patch("tools.news_data.NewsApiClient") as mock_client:
        mock_client.return_value.get_everything.side_effect = Exception("API error")
        from tools.news_data import fetch_news

        result = fetch_news("AAPL", api_key="test_key")
        assert result == []


def test_fetch_news_returns_list_of_dicts_on_success():
    """fetch_news should return a list of article dicts with expected keys."""
    mock_response = {
        "articles": [
            {
                "title": "Apple reports record earnings",
                "description": "Apple Inc reported record quarterly earnings.",
                "content": "Full article content here.",
                "source": {"name": "Reuters"},
                "publishedAt": "2026-10-01T00:00:00Z",
            }
        ]
    }
    with patch("tools.news_data.NewsApiClient") as mock_client:
        mock_client.return_value.get_everything.return_value = mock_response
        from tools.news_data import fetch_news

        result = fetch_news("AAPL", api_key="test_key")
        assert len(result) == 1
        assert result[0]["title"] == "Apple reports record earnings"
        assert result[0]["source"] == "Reuters"
