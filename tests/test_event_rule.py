from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.event_rule import EventRule
from configuration_engine.rules.recommendation_rule import (
    ACCESS_READ_ONLY,
    ACCESS_READ_WRITE,
)


def test_overheat_is_event() -> None:
    property = DeviceProperty(
        name="overheat",
        property="overheat",
        label="Overheat",
        property_type="enum",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Overheat status.",
        unit=None,
        values=["Normal", "Overheated"],
    )

    recommendation = EventRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.EVENT,
        apply=False,
    )


def test_writable_overheat_is_not_event() -> None:
    property = DeviceProperty(
        name="overheat",
        property="overheat",
        label="Overheat",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category=None,
        description="Overheat status.",
        unit=None,
        values=["Normal", "Overheated"],
    )

    recommendation = EventRule().recommend(property)

    assert recommendation is None


def test_unrelated_read_only_property_is_not_event() -> None:
    property = DeviceProperty(
        name="temperature",
        property="temperature",
        label="Temperature",
        property_type="numeric",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Current temperature.",
        unit="°C",
        values=[],
    )

    recommendation = EventRule().recommend(property)

    assert recommendation is None
