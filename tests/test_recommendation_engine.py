from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation_engine import RecommendationEngine
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.recommendation_rule import ACCESS_COMMAND, ACCESS_READ_WRITE


def test_binding_rule_wins_over_configuration_rule() -> None:
    property = DeviceProperty(
        name="bindingOffToOnSyncLevel",
        property="bindingOffToOnSyncLevel",
        label="Binding Off To On Sync Level",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category="config",
        description="Send a level to bound devices.",
        unit=None,
        values=["Disabled", "Enabled"],
    )

    recommendation = RecommendationEngine().recommend(property)

    assert recommendation.include is False
    assert recommendation.confidence == Confidence.CERTAIN
    assert recommendation.reason == RecommendationReason.BINDING_RELATED
    assert recommendation.apply is False


def test_command_rule_is_reached() -> None:
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

    recommendation = RecommendationEngine().recommend(property)

    assert recommendation.include is True
    assert recommendation.confidence == Confidence.CERTAIN
    assert recommendation.reason == RecommendationReason.COMMAND
    assert recommendation.apply is False


def test_unmatched_property_is_unknown() -> None:
    property = DeviceProperty(
        name="somethingUnknown",
        property="somethingUnknown",
        label="Something Unknown",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category=None,
        description="No rule should recognize this property.",
        unit=None,
        values=["A", "B"],
    )

    recommendation = RecommendationEngine().recommend(property)

    assert recommendation.include is False
    assert recommendation.confidence == Confidence.NONE
    assert recommendation.reason == RecommendationReason.UNKNOWN
