from __future__ import annotations

from configuration_engine.recommendation import Recommendation


class RecommendationFormatter:
    """Format property recommendations."""

    @staticmethod
    def format(
        recommendations: list[Recommendation],
    ) -> str:
        lines: list[str] = []

        for recommendation in recommendations:
            lines.append(recommendation.property.name)
            lines.append(
                f"    Recommendation : {'Include' if recommendation.include else 'Exclude'}"
            )
            lines.append(
                f"    Confidence     : {recommendation.confidence.description} "
                f"({int(recommendation.confidence)}%)"
            )
            lines.append(f"    Reason         : {recommendation.reason.value}")
            lines.append("")

        return "\n".join(lines)
