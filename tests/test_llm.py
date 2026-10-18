# tests/test_llm.py
"""
Contract tests for the call_llm wrapper defined in tools/llm.py.

Validates retry behavior without making live API calls. time.sleep is patched
so the tests run instantly. Run with:

    python -m pytest tests/test_llm.py -v
"""

from unittest.mock import patch

import pytest

from tools.llm import TransientLLMError, call_llm


def test_call_llm_retries_on_transient_failure():
    """call_llm should retry transient failures and succeed if the provider
    recovers within three attempts, waiting 5s and then 10s."""
    outcomes = [TransientLLMError("503"), TransientLLMError("503"), "success"]

    with patch("tools.llm._call_gemini", side_effect=outcomes) as mock_gemini, \
         patch("tools.llm.time.sleep") as mock_sleep:
        result = call_llm("test prompt")

    assert result == "success"
    assert mock_gemini.call_count == 3
    assert [c.args[0] for c in mock_sleep.call_args_list] == [5, 10]


def test_call_llm_raises_after_max_retries():
    """call_llm should raise after exhausting all three attempts."""
    with patch("tools.llm._call_gemini",
               side_effect=TransientLLMError("503 server error")) as mock_gemini, \
         patch("tools.llm.time.sleep") as mock_sleep:
        with pytest.raises(TransientLLMError, match="503 server error"):
            call_llm("test prompt")

    assert mock_gemini.call_count == 3
    assert mock_sleep.call_count == 2


def test_call_llm_does_not_retry_value_error():
    """call_llm should not retry configuration errors such as an unsupported
    provider."""
    with patch("tools.llm.LLM_PROVIDER", "unsupported"), \
         patch("tools.llm.time.sleep") as mock_sleep:
        with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
            call_llm("test prompt")

    mock_sleep.assert_not_called()


def test_call_llm_does_not_retry_non_transient_errors():
    """call_llm should fail on the first attempt for errors that retrying
    cannot fix, such as an invalid API key or an unknown model."""
    with patch("tools.llm._call_gemini",
               side_effect=RuntimeError("invalid API key")) as mock_gemini, \
         patch("tools.llm.time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError, match="invalid API key"):
            call_llm("test prompt")

    assert mock_gemini.call_count == 1
    mock_sleep.assert_not_called()
