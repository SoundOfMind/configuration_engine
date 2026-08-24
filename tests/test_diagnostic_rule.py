from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.diagnostic_rule import DiagnosticRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ_ONLY, ACCESS_READ_WRITE


def test_diagnostic_property_is_excluded() -> None:
    property = DeviceProperty(
        name="internalTemperature",
        property="internalTemperature",
        label="Internal Temperature",
        property_type="numeric",
        access=ACCESS_READ_ONLY,
        category="diagnostic",
        description="Current internal temperature.",
        unit="°C",
        values=[],
    )

    recommendation = DiagnosticRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=False,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.DIAGNOSTIC,
        apply=False,
    )


def test_non_diagnostic_property_is_not_classified() -> None:
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

    recommendation = DiagnosticRule().recommend(property)

    assert recommendation is None
