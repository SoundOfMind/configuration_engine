from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.measurement_rule import MeasurementRule
from configuration_engine.rules.recommendation_rule import (
    ACCESS_READ,
    ACCESS_READ_ONLY,
    ACCESS_READ_WRITE,
)


def test_read_only_numeric_property_with_unit_is_measurement() -> None:
    property = DeviceProperty(
        name="power",
        property="power",
        label="Power",
        property_type="numeric",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Instantaneous measured power",
        unit="W",
        values=[],
    )

    recommendation = MeasurementRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=False,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.MEASUREMENT,
    )


def test_writable_numeric_property_is_not_measurement() -> None:
    property = DeviceProperty(
        name="brightness",
        property="brightness",
        label="Brightness",
        property_type="numeric",
        access=ACCESS_READ_WRITE,
        category=None,
        description="Set brightness",
        unit="%",
        values=[],
    )

    assert MeasurementRule().recommend(property) is None


def test_read_only_numeric_property_without_unit_is_not_measurement() -> None:
    property = DeviceProperty(
        name="internal_value",
        property="internal_value",
        label="Internal Value",
        property_type="numeric",
        access=ACCESS_READ,
        category=None,
        description="Internal device value",
        unit=None,
        values=[],
    )

    assert MeasurementRule().recommend(property) is None
