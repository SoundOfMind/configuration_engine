from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import (
    ACCESS_READ_ONLY,
    RecommendationRule,
)


class MeasurementRule(RecommendationRule):
    """Recommend excluding read-only measurement properties."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation when metadata identifies a measurement."""

        if property.access != ACCESS_READ_ONLY:
            return None

        if property.property_type != "numeric":
            return None

        if property.unit is None:
            return None

        return Recommendation(
            property=property,
            include=False,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.MEASUREMENT,
            apply=False,
        )
