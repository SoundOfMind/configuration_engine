from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import RecommendationRule


class InstallationRule(RecommendationRule):
    """Recommend physical installation information for display."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for installation topology."""
        # Installation topology is device information. It should be
        # displayed but never applied to another device.

        if property.property_type != "enum":
            return None

        if property.name == "powerType":
            return Recommendation(
                property=property,
                include=True,
                confidence=Confidence.CERTAIN,
                reason=RecommendationReason.DEVICE_INFORMATION,
                apply=False,
            )

        values = {value.casefold().replace("_", " ").strip() for value in property.values}

        if not any(
            phrase in value
            for value in values
            for phrase in (
                "single pole",
                "3-way",
                "3 way",
            )
        ):
            return None

        return Recommendation(
            property=property,
            include=True,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.PRESERVED,
            apply=False,
        )
