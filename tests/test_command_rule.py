from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.command_rule import CommandRule
from configuration_engine.rules.recommendation_rule import ACCESS_COMMAND


def test_command_property_is_included() -> None:
    property = DeviceProperty(
        name="identify",
        property="identify",
        label="Identify",
        property_type="enum",
        access=ACCESS_COMMAND,
        category=None,
        description="Identify the device.",
        unit=None,
        values=["start"],
    )

    recommendation = CommandRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.COMMAND,
        apply=False,
    )


def test_unknown_command_property_is_not_classified() -> None:
    property = DeviceProperty(
        name="someOtherCommand",
        property="someOtherCommand",
        label="Some Other Command",
        property_type="enum",
        access=ACCESS_COMMAND,
        category=None,
        description="An unknown command.",
        unit=None,
        values=["start"],
    )

    recommendation = CommandRule().recommend(property)

    assert recommendation is None
