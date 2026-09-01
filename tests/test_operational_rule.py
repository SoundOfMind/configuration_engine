from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.operational_rule import OperationalRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ, ACCESS_READ_WRITE


def test_state_is_operational() -> None:
    property = DeviceProperty(
        name="state",
        property="state",
        label="State",
        property_type="binary",
        access=ACCESS_READ_WRITE,
        category=None,
        description="Current on/off state.",
        unit=None,
        values=[],
    )

    recommendation = OperationalRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.OPERATIONAL,
        apply=False,
    )


def test_brightness_is_operational() -> None:
    property = DeviceProperty(
        name="brightness",
        property="brightness",
        label="Brightness",
        property_type="numeric",
        access=ACCESS_READ_WRITE,
        category=None,
        description="Current brightness level.",
        unit=None,
        values=[],
    )

    recommendation = OperationalRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.OPERATIONAL,
        apply=True,
    )


def test_unrelated_property_is_not_operational() -> None:
    property = DeviceProperty(
        name="power_on_behavior",
        property="power_on_behavior",
        label="Power On Behavior",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category="config",
        description="Controls behavior after power loss.",
        unit=None,
        values=["off", "previous", "on"],
    )

    recommendation = OperationalRule().recommend(property)

    assert recommendation is None


def test_state_must_be_read_write() -> None:
    property = DeviceProperty(
        name="state",
        property="state",
        label="State",
        property_type="binary",
        access=ACCESS_READ,
        category=None,
        description="Current on/off state.",
        unit=None,
        values=[],
    )

    recommendation = OperationalRule().recommend(property)

    assert recommendation is None
