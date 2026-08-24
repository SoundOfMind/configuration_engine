from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason

from .recommendation_rule import RecommendationRule


class ProtectionRule(RecommendationRule):
    """Recommend read-only protection settings for display."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for a protection property."""

        if property.access != 5:
            return None

        text = " ".join(
            part
            for part in (
                property.name,
                property.label,
                property.description,
            )
            if part
        ).lower()

        if "protection" not in text:
            return None

        return Recommendation(
            property=property,
            include=True,
            confidence=Confidence.HIGH,
            reason=RecommendationReason.DEVICE_INFORMATION,
            apply=False,
        )
