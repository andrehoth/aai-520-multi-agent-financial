# tests/test_schema_contract.py
"""
Contract tests for the inter-agent data schema defined in agents/schema.py.

Both teammates maintain this contract so that chain output and agent interfaces
are validated against the same schema definition. Run with:

    python -m pytest tests/test_schema_contract.py -v
"""

from agents.schema import ANALYSIS_SCHEMA, ContentType, empty_analysis


def test_empty_analysis_matches_schema():
    """empty_analysis should contain exactly the fields in ANALYSIS_SCHEMA."""
    analysis = empty_analysis("AAPL")

    assert set(analysis.keys()) == set(ANALYSIS_SCHEMA.keys())


def test_empty_analysis_preserves_ticker():
    """empty_analysis should preserve the supplied stock ticker."""
    analysis = empty_analysis("AAPL")

    assert analysis["ticker"] == "AAPL"


def test_empty_analysis_field_types_match_schema():
    """Each initialized field should match its declared schema type."""
    analysis = empty_analysis("AAPL")

    for field, expected_type in ANALYSIS_SCHEMA.items():
        assert isinstance(analysis[field], expected_type)


def test_empty_analysis_initial_values():
    """Pipeline output fields should start empty with a zero evaluation score."""
    analysis = empty_analysis("AAPL")

    assert analysis["earnings_analysis"] == ""
    assert analysis["news_analysis"] == ""
    assert analysis["market_analysis"] == ""
    assert analysis["synthesis"] == ""
    assert analysis["evaluation_score"] == 0.0
    assert analysis["evaluation_feedback"] == ""
    assert analysis["reflection"] == ""
    assert analysis["timestamp"] == ""


def test_content_type_enum_has_all_values():
    """ContentType must contain NEWS, EARNINGS, MARKET, and MACRO."""
    values = [ct.value for ct in ContentType]

    assert "NEWS" in values
    assert "EARNINGS" in values
    assert "MARKET" in values
    assert "MACRO" in values


def test_content_type_values_are_uppercase():
    """All ContentType enum values must be uppercase strings."""
    for ct in ContentType:
        assert ct.value == ct.value.upper()
