from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.binding_rule import BindingRule
from configuration_engine.rules.configuration_rule import ConfigurationRule
from configuration_engine.rules.recommendation_rule import ACCESS_READ_WRITE


def test_configuration_property_is_included() -> None:
    property = DeviceProperty(
        name="power_on_behavior",
        property="power_on_behavior",
        label="PowerOnBehavior",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category="config",
        description="Controls behavior after power loss.",
        unit=None,
        values=["off", "previous", "on"],
    )

    recommendation = ConfigurationRule().recommend(property)

    assert recommendation == Recommendation(
        property=property,
        include=True,
        confidence=Confidence.CERTAIN,
        reason=RecommendationReason.CONFIGURATION,
        apply=True,
    )


def test_binding_related_configuration_is_excluded() -> None:
    property = DeviceProperty(
        name="bindingOffToOnSyncLevel",
        property="bindingOffToOnSyncLevel",
        label="BindingOffToOnSyncLevel",
        property_type="enum",
        access=ACCESS_READ_WRITE,
        category="config",
        description=("Send Move_To_Level using Default Level with Off/On to bound devices."),
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
