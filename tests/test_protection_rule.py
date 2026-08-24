from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.protection_rule import ProtectionRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ_ONLY, ACCESS_READ_WRITE


def test_read_only_protection_property_is_included() -> None:
    property = DeviceProperty(
        name="protection",
        property="protection",
        label="Protection",
        property_type="enum",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Current protection state.",
        unit=None,
        values=["None", "Local", "Bypass"],
    )

    recommendation = ProtectionRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.HIGH,
        reason=RecommendationReason.DEVICE_INFORMATION,
        apply=False,
    )


def test_writable_protection_property_is_not_classified() -> None:
    property = DeviceProperty(
        name="protection",
        property="protection",
        label="Protection",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category="config",
        description="Protection setting.",
        unit=None,
        values=["None", "Local", "Bypass"],
    )

    recommendation = ProtectionRule().recommend(property)

    assert recommendation is None


def test_unrelated_read_only_property_is_not_classified() -> None:
    property = DeviceProperty(
        name="temperature",
        property="temperature",
        label="Temperature",
        property_type="numeric",
        access=ACCESS_READ_ONLY,
        category="diagnostic",
        description="Current internal temperature.",
        unit="°C",
        values=[],
    )

    recommendation = ProtectionRule().recommend(property)

    assert recommendation is None
