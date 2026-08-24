from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PropertyDifference:
    """Difference between two property values."""

    property_name: str
    current_value: Any
    desired_value: Any


@dataclass(frozen=True, slots=True)
class ProfileDifference:
    """Collection of differences between two profiles."""

    differences: list[PropertyDifference]

    @property
    def is_empty(self) -> bool:
        """Return True if no differences exist."""
        return not self.differences
