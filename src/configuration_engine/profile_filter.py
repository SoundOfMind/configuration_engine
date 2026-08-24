from __future__ import annotations

from configuration_engine.device_definition import DeviceDefinition
from configuration_engine.profile import Profile
from configuration_engine.recommendation_engine import RecommendationEngine


class ProfileFilter:
    """Select properties from a profile that may be applied."""

    def __init__(self) -> None:
        self._engine = RecommendationEngine()

    def filter(
        self,
        profile: Profile,
        definition: DeviceDefinition,
    ) -> Profile:
        """Return the portion of a profile that may be applied."""

        properties = {property.name: property for property in definition.properties}

        values: dict[str, object] = {}

        for name, value in profile.values.items():
            property = properties.get(name)

            if property is None:
                continue

            recommendation = self._engine.recommend(property)

            if recommendation.apply:
                values[name] = value

        return Profile(
            vendor=profile.vendor,
            model=profile.model,
            values=values,
        )
