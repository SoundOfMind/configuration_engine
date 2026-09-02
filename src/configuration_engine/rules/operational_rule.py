from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import (
    ACCESS_READ_WRITE,
    RecommendationRule,
)


class OperationalRule(RecommendationRule):
    """Recommend operational control properties."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for an operational control property."""

        if property.name.casefold() == "state":
            if property.access != ACCESS_READ_WRITE:
                return None

            return Recommendation(
                property=property,
                include=True,
                confidence=Confidence.CERTAIN,
                reason=RecommendationReason.OPERATIONAL,
                apply=False,
            )

        if property.name.casefold() == "brightness":
            if property.access != ACCESS_READ_WRITE:
                return None

            return Recommendation(
                property=property,
                include=True,
                confidence=Confidence.CERTAIN,
                reason=RecommendationReason.OPERATIONAL,
                apply=True,
            )

        return None
