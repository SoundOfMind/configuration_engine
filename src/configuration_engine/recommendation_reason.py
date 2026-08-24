from __future__ import annotations

from enum import Enum, auto


class RecommendationReason(Enum):
    """Reason for a recommendation."""

    CONFIGURATION = auto()
    DIAGNOSTIC = auto()
    BINDING_RELATED = auto()
    MEASUREMENT = auto()
    COMMAND = auto()
    EVENT = auto()
    OPERATIONAL = auto()
    DEFAULT = auto()
    DEVICE_INFORMATION = auto()
    PRESERVED = auto()
    UNKNOWN = auto()

    @property
    def title(self) -> str:
        """Return a human-readable title."""
        match self:
            case RecommendationReason.CONFIGURATION:
                return "Configuration property."

            case RecommendationReason.DIAGNOSTIC:
                return "Diagnostic property."

            case RecommendationReason.BINDING_RELATED:
                return "Binding-related configuration."

            case RecommendationReason.MEASUREMENT:
                return "Read-only measurement."

            case RecommendationReason.COMMAND:
                return "Command property."

            case RecommendationReason.EVENT:
                return "Event property."

            case RecommendationReason.OPERATIONAL:
                return "Operational property."

            case RecommendationReason.DEFAULT:
                return "Included by default."

            case RecommendationReason.DEVICE_INFORMATION:
                return "Informational device property."

            case RecommendationReason.PRESERVED:
                return "Preserved device property."

            case RecommendationReason.UNKNOWN:
                return "Unable to classify property."

        raise AssertionError("Unhandled RecommendationReason.")
