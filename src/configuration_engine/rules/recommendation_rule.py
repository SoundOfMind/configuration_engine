from __future__ import annotations

from abc import ABC, abstractmethod

from configuration_engine.device_definition import DeviceProperty
from configuration_engine.property_classifier import PropertyClassifier
from configuration_engine.recommendation import Recommendation

ACCESS_READ = 1
ACCESS_COMMAND = 2
ACCESS_READ_ONLY = 5
ACCESS_READ_WRITE = 7


class RecommendationRule(ABC):
    """Base class for recommendation rules."""

    def __init__(self) -> None:
        self.classifier = PropertyClassifier()

    @abstractmethod
    def recommend(
        self,
        property: DeviceProperty,
    ) -> Recommendation | None:
        """
        Return a recommendation if this rule applies.

        Return None to allow the next rule to evaluate the property.
        """
