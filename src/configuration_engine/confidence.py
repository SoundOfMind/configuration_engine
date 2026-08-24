from __future__ import annotations

from enum import IntEnum


class Confidence(IntEnum):
    """Recommendation confidence."""

    NONE = 0
    LOW = 35
    MEDIUM = 60
    HIGH = 85
    VERY_HIGH = 95
    CERTAIN = 100

    @property
    def description(self) -> str:
        """Return a human-readable confidence description."""

        match self:
            case Confidence.NONE:
                return "None"

            case Confidence.LOW:
                return "Low"

            case Confidence.MEDIUM:
                return "Medium"

            case Confidence.HIGH:
                return "High"

            case Confidence.VERY_HIGH:
                return "Very High"

            case Confidence.CERTAIN:
                return "Certain"

        raise AssertionError("Unhandled Confidence value.")
