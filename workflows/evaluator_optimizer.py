"""Evaluator-optimizer workflow for investment analysis refinement."""

from tools.llm import call_llm


class EvaluatorOptimizer:
    """Evaluate and refine synthesized investment analysis."""

    def __init__(self, ticker: str):
        self.ticker = ticker

    def evaluate(self, synthesis: str) -> tuple[float, str]:
        """Evaluate a synthesized investment analysis and return score and feedback."""
        if not synthesis:
            return 0.0, "No synthesis was provided for evaluation."

        prompt = (
            f"Evaluate the following investment analysis for {self.ticker}.\n\n"
            f"{synthesis}\n\n"
            "Evaluate the analysis for factual grounding, completeness, clarity, "
            "balance, and support for its conclusions.\n\n"
            "Assign an overall score from 0 to 10, where 10 represents an "
            "exceptionally strong analysis. Provide specific feedback identifying "
            "strengths and areas that should be improved.\n\n"
            "Return your response in exactly this format:\n"
            "SCORE: <number from 0 to 10>\n"
            "FEEDBACK: <specific feedback>"
        )

        response = call_llm(
            prompt=prompt,
            system=(
                "You are a rigorous evaluator of financial research. "
                "Assess only the supplied analysis and do not introduce new facts."
            ),
            temperature=0.2,
        )

        score = 0.0
        feedback = response.strip()

        for line in response.splitlines():
            if line.startswith("SCORE:"):
                try:
                    score_str = line.split(":", 1)[1].strip()
                    score = float(score_str.split("/")[0].strip())
                except ValueError:
                    score = 0.0
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()

        score = max(0.0, min(10.0, score))

        return score, feedback

    def refine(self, synthesis: str, feedback: str) -> str:
        """Refine a synthesized investment analysis using evaluator feedback."""
        if not synthesis:
            return ""

        if not feedback:
            return synthesis

        prompt = (
            f"Refine the following investment analysis for {self.ticker}.\n\n"
            f"ORIGINAL ANALYSIS:\n{synthesis}\n\n"
            f"EVALUATOR FEEDBACK:\n{feedback}\n\n"
            "Revise the analysis to address the evaluator feedback while "
            "preserving supported facts and important uncertainty. Improve "
            "clarity, completeness, balance, and support for conclusions. "
            "Do not invent facts, sources, financial figures, or events that "
            "are not contained in the original analysis."
        )

        return call_llm(
            prompt=prompt,
            system=(
                "You are a financial research editor. Improve the supplied "
                "investment analysis using the evaluator feedback while remaining "
                "strictly grounded in the original analysis."
            ),
            temperature=0.2,
        )

    def run(self, analysis: dict) -> dict:
        """Evaluate and refine the synthesis in the shared analysis dictionary."""
        synthesis = analysis.get("synthesis", "")

        score, feedback = self.evaluate(synthesis)

        analysis["evaluation_score"] = score
        analysis["evaluation_feedback"] = feedback

        if synthesis and feedback:
            analysis["synthesis"] = self.refine(synthesis, feedback)

        return analysis
