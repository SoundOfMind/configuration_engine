from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import ACCESS_READ_ONLY, RecommendationRule


class EventRule(RecommendationRule):
    """Recommend device event and status properties for display."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for an event property."""

        if property.name != "overheat":
            return None

        if property.access != ACCESS_READ_ONLY:
            return None

        return Recommendation(
            property=property,
            include=True,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.EVENT,
            apply=False,
        )
