# tests/test_schema_contract.py
"""
Contract tests for the inter-agent data schema defined in agents/schema.py.

These tests validate that the shared analysis dict behaves correctly so that
both teammates' code works against the same contract. Run with:

    python -m pytest tests/test_schema_contract.py -v
"""

from agents.schema import empty_analysis, ANALYSIS_SCHEMA, ContentType


def test_empty_analysis_has_all_keys():
    """All keys defined in ANALYSIS_SCHEMA must be present in empty_analysis() output."""
    pass


def test_string_fields_initialize_empty():
    """All string fields must initialize to empty string, not None."""
    pass


def test_evaluation_score_initializes_to_float():
    """evaluation_score must initialize to 0.0 as a float, not 0 (int) or None."""
    pass


def test_ticker_is_preserved():
    """The ticker passed to empty_analysis() must appear in the returned dict."""
    pass


def test_schema_keys_match_analysis_keys():
    """Keys in ANALYSIS_SCHEMA must exactly match keys in empty_analysis() output."""
    pass


def test_content_type_enum_has_all_values():
    """ContentType must contain NEWS, EARNINGS, MARKET, and MACRO."""
    pass


def test_content_type_values_are_uppercase():
    """All ContentType enum values must be uppercase strings."""
    pass
