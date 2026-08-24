from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import (
    ACCESS_COMMAND,
    RecommendationRule,
)


class CommandRule(RecommendationRule):
    """Recommend command properties for display."""

    # Commands are displayed for awareness but are not replayed when
    # applying a profile.

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """Return a recommendation for a command property."""

        if property.access != ACCESS_COMMAND:
            return None

        if property.name not in {
            "identify",
            "energy_reset",
        }:
            return None

        return Recommendation(
            property=property,
            include=True,
            confidence=Confidence.CERTAIN,
            reason=RecommendationReason.COMMAND,
            apply=False,
        )
