from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import RecommendationRule


class DiagnosticRule(RecommendationRule):
    """Recommend excluding diagnostic properties."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:

        if not self.classifier.is_diagnostic(property):
            return None

        return Recommendation(
            property=property,
            include=False,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.DIAGNOSTIC,
        )
