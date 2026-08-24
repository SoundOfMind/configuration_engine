from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import (
    ACCESS_READ_ONLY,
    RecommendationRule,
)


class BindingRule(RecommendationRule):
    """Recommend binding-related properties."""

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for a binding-related property."""

        if property.name == "deviceBindNumber":
            # Binding count is useful device information, but must never
            # be copied as configuration to another device.

            if property.access != ACCESS_READ_ONLY:
                return None

            return Recommendation(
                property=property,
                include=True,
                confidence=Confidence.HIGH,
                reason=RecommendationReason.DEVICE_INFORMATION,
                apply=False,
            )

        if self._is_binding_configuration(property):
            # Binding configuration is device-specific and unsafe to
            # reproduce when applying a profile to another device.

            return Recommendation(
                property=property,
                include=False,
                confidence=Confidence.CERTAIN,
                reason=RecommendationReason.BINDING_RELATED,
                apply=False,
            )

        return None

    @staticmethod
    def _is_binding_configuration(
        property: DeviceProperty,
    ) -> bool:
        text = " ".join(
            part
            for part in (
                property.name,
                property.label,
                property.description,
            )
            if part
        ).casefold()

        return "binding" in text or "bound device" in text
