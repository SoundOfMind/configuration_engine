from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.installation_rule import InstallationRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ_ONLY


def test_power_type_is_included_as_device_information() -> None:
    property = DeviceProperty(
        name="powerType",
        property="powerType",
        label="PowerType",
        property_type="enum",
        access=ACCESS_READ_ONLY,
        category=None,
        description="Set the power type for the device.",
        unit=None,
        values=["Non Neutral", "Neutral"],
    )

    recommendation = InstallationRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.DEVICE_INFORMATION,
        apply=False,
    )


def test_three_way_is_preserved() -> None:
    property = DeviceProperty(
        name="switchType",
        property="switchType",
        label="Switch Type",
        property_type="enum",
        access=3,
        category="config",
        description="Select the switch type.",
        unit=None,
        values=["single pole", "3-way"],
    )

    recommendation = InstallationRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.PRESERVED,
        apply=False,
    )
