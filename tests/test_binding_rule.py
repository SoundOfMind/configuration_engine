from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.binding_rule import BindingRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ_ONLY, ACCESS_READ_WRITE


def test_device_bind_number_is_device_information() -> None:
    property = DeviceProperty(
        name="deviceBindNumber",
        property="deviceBindNumber",
        label="Device Bind Number",
        property_type="numeric",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Number of bindings for this device.",
        unit=None,
        values=[],
    )

    recommendation = BindingRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.HIGH,
        reason=RecommendationReason.DEVICE_INFORMATION,
        apply=False,
    )


def test_binding_configuration_is_excluded() -> None:
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

    recommendation = BindingRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=False,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.BINDING_RELATED,
        apply=False,
    )


def test_unrelated_property_is_not_classified() -> None:
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

    recommendation = BindingRule().recommend(property)

    assert recommendation is None
