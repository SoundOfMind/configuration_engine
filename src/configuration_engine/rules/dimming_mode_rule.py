from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason

from .recommendation_rule import RecommendationRule


class DimmingModeRule(RecommendationRule):
    """Recommend read-only dimming-mode information for display."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for a read-only dimming-mode property."""

        if property.access != 5:
            return None

        if property.property_type != "enum":
            return None

        values = {value.lower() for value in property.values}

        if not {"leading edge", "trailing edge"} <= values:
            return None

        return Recommendation(
            property=property,
            include=True,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.DEVICE_INFORMATION,
            apply=False,
        )
