from __future__ import annotations

from dataclasses import dataclass

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation_reason import RecommendationReason


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Engine recommendation for a device property."""

    property: DeviceProperty
    include: bool
    confidence: Confidence
    reason: RecommendationReason
    apply: bool = False
