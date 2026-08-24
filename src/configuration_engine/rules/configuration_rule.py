from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import RecommendationRule


class ConfigurationRule(RecommendationRule):
    """Recommend explicitly identified configuration properties."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation when metadata identifies configuration."""

        if property.category != "config":
            return None

        return Recommendation(
            property=property,
            include=True,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.CONFIGURATION,
            apply=True,
        )
