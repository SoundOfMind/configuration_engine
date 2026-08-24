from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PropertyMetadata:
    """Describes a configurable property."""

    writable: bool = True
    display_name: str | None = None
