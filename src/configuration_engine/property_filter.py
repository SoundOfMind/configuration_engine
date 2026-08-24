from __future__ import annotations

from configuration_engine.device_definition import DeviceDefinition
from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_engine import RecommendationEngine


class PropertyFilter:
    """Select properties to include in a captured profile."""

    def __init__(self) -> None:
        self._engine = RecommendationEngine()

    def filter(
        self,
        definition: DeviceDefinition,
        snapshot: DeviceSnapshot,
    ) -> dict[str, object]:
        """Return the properties to include in the profile."""

        values: dict[str, object] = {}

        for recommendation in self.decisions(
            definition,
            snapshot,
        ):
            if recommendation.include:
                values[recommendation.property.name] = snapshot.values[recommendation.property.name]

        return values

    def decisions(
        self,
        definition: DeviceDefinition,
        snapshot: DeviceSnapshot,
    ) -> list[Recommendation]:
        """Return recommendations for every property."""

        recommendations: list[Recommendation] = []

        for property in definition.properties:
            if property.name not in snapshot.values:
                continue

            recommendations.append(self._engine.recommend(property))

        return recommendations
