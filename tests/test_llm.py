# tests/test_llm.py
"""
Contract tests for the call_llm wrapper defined in tools/llm.py.

Validates retry behavior on transient failures without making live API calls.
Run with:

    python -m pytest tests/test_llm.py -v
"""

from unittest.mock import patch, MagicMock
import pytest


def test_call_llm_retries_on_transient_failure():
    """call_llm should retry up to 3 times on transient errors and succeed
    if the provider recovers before max retries are exhausted."""
    responses = [
        Exception("503 server error"),
        Exception("503 server error"),
        "success",
    ]

    def side_effect(*args, **kwargs):
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    with patch("tools.llm._call_gemini", side_effect=side_effect), patch(
        "tools.llm.time.sleep"
    ):
        from tools.llm import call_llm

        result = call_llm("test prompt")
        assert result == "success"


def test_call_llm_raises_after_max_retries():
    """call_llm should raise after exhausting all retries."""
    with patch(
        "tools.llm._call_gemini", side_effect=Exception("503 server error")
    ), patch("tools.llm.time.sleep"):
        from tools.llm import call_llm

        with pytest.raises(Exception, match="503 server error"):
            call_llm("test prompt")


def test_call_llm_does_not_retry_value_error():
    """call_llm should not retry configuration errors such as unsupported provider."""
    with patch("tools.llm.LLM_PROVIDER", "unsupported"):
        from tools.llm import call_llm

        with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
            call_llm("test prompt")
