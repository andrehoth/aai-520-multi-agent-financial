from unittest.mock import Mock

from workflows.evaluator_optimizer import EvaluatorOptimizer


def test_stops_immediately_when_threshold_is_met():
    optimizer = EvaluatorOptimizer(
        ticker="AAPL",
        threshold=7.0,
        max_iterations=3,
    )

    optimizer.evaluate = Mock(
        return_value=(8.0, "Analysis already meets the quality threshold.")
    )
    optimizer.refine = Mock()

    analysis = {
        "synthesis": "Original investment analysis."
    }

    result = optimizer.run(analysis)

    assert result["evaluation_score"] == 8.0
    assert result["evaluation_feedback"] == (
        "Analysis already meets the quality threshold."
    )
    assert result["synthesis"] == "Original investment analysis."

    optimizer.evaluate.assert_called_once_with(
        "Original investment analysis."
    )
    optimizer.refine.assert_not_called()


def test_refines_until_threshold_is_met():
    optimizer = EvaluatorOptimizer(
        ticker="AAPL",
        threshold=7.0,
        max_iterations=3,
    )

    optimizer.evaluate = Mock(
        side_effect=[
            (5.5, "Analysis needs stronger support."),
            (7.5, "Analysis now meets the quality threshold."),
        ]
    )
    optimizer.refine = Mock(
        return_value="Refined investment analysis."
    )

    analysis = {
        "synthesis": "Original investment analysis."
    }

    result = optimizer.run(analysis)

    assert result["evaluation_score"] == 7.5
    assert result["evaluation_feedback"] == (
        "Analysis now meets the quality threshold."
    )
    assert result["synthesis"] == "Refined investment analysis."

    assert optimizer.evaluate.call_count == 2
    optimizer.refine.assert_called_once_with(
        "Original investment analysis.",
        "Analysis needs stronger support.",
    )


def test_stops_at_max_iterations_when_threshold_is_not_met():
    optimizer = EvaluatorOptimizer(
        ticker="AAPL",
        threshold=7.0,
        max_iterations=3,
    )

    optimizer.evaluate = Mock(
        side_effect=[
            (5.0, "First evaluation feedback."),
            (6.0, "Second evaluation feedback."),
            (6.5, "Final evaluation feedback."),
        ]
    )

    optimizer.refine = Mock(
        side_effect=[
            "First refined analysis.",
            "Second refined analysis.",
        ]
    )

    analysis = {
        "synthesis": "Original investment analysis."
    }

    result = optimizer.run(analysis)

    assert result["evaluation_score"] == 6.5
    assert result["evaluation_feedback"] == (
        "Final evaluation feedback."
    )
    assert result["synthesis"] == "Second refined analysis."

    assert optimizer.evaluate.call_count == 3
    assert optimizer.refine.call_count == 2