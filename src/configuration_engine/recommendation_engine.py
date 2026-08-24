from __future__ import annotations

from configuration_engine.confidence import Confidence
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.recommendation import Recommendation
from configuration_engine.recommendation_reason import RecommendationReason
from configuration_engine.rules.binding_rule import BindingRule
from configuration_engine.rules.command_rule import CommandRule
from configuration_engine.rules.configuration_rule import ConfigurationRule
from configuration_engine.rules.diagnostic_rule import DiagnosticRule
from configuration_engine.rules.dimming_mode_rule import DimmingModeRule
from configuration_engine.rules.event_rule import EventRule
from configuration_engine.rules.installation_rule import InstallationRule
from configuration_engine.rules.measurement_rule import MeasurementRule
from configuration_engine.rules.operational_rule import OperationalRule
from configuration_engine.rules.protection_rule import ProtectionRule
from configuration_engine.rules.recommendation_rule import RecommendationRule


class RecommendationEngine:
    """Generate property recommendations from device metadata."""

    def __init__(self) -> None:
        self._rules: list[RecommendationRule] = [
            DiagnosticRule(),
            DimmingModeRule(),
            InstallationRule(),
            ProtectionRule(),
            MeasurementRule(),
            OperationalRule(),
            EventRule(),
            BindingRule(),
            CommandRule(),
            ConfigurationRule(),
        ]

    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation:
        """Return the engine recommendation for a property."""

        for rule in self._rules:
            recommendation = rule.recommend(property)

            if recommendation is not None:
                return recommendation

        return Recommendation(
            property=property,
            include=False,
            confidence=Confidence.NONE,
            reason=RecommendationReason.UNKNOWN,
        )
