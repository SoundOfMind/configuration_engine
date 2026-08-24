from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.dimming_mode_rule import DimmingModeRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ_ONLY, ACCESS_READ_WRITE


def test_dimming_mode_is_included() -> None:
    property = DeviceProperty(
        name="dimmingMode",
        property="dimmingMode",
        label="Dimming Mode",
        property_type="enum",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Dimming mode.",
        unit=None,
        values=["Leading Edge", "Trailing Edge"],
    )

    recommendation = DimmingModeRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.DEVICE_INFORMATION,
        apply=False,
    )


def test_dimming_mode_values_are_case_insensitive() -> None:
    property = DeviceProperty(
        name="dimmingMode",
        property="dimmingMode",
        label="Dimming Mode",
        property_type="enum",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Dimming mode.",
        unit=None,
        values=["LEADING EDGE", "trailing edge"],
    )

    recommendation = DimmingModeRule().recommend(property)

    assert recommendation is not None
    assert recommendation.include is True
    assert recommendation.confidence == Confidence.CERTAIN
    assert recommendation.reason == RecommendationReason.DEVICE_INFORMATION
    assert recommendation.apply is False


def test_missing_dimming_mode_value_is_not_classified() -> None:
    property = DeviceProperty(
        name="dimmingMode",
        property="dimmingMode",
        label="Dimming Mode",
        property_type="enum",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Dimming mode.",
        unit=None,
        values=["Leading Edge", "Off"],
    )

    recommendation = DimmingModeRule().recommend(property)

    assert recommendation is None


def test_writable_dimming_mode_is_not_classified() -> None:
    property = DeviceProperty(
        name="dimmingMode",
        property="dimmingMode",
        label="Dimming Mode",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category="config",
        description="Dimming mode.",
        unit=None,
        values=["Leading Edge", "Trailing Edge"],
    )

    recommendation = DimmingModeRule().recommend(property)

    assert recommendation is None
