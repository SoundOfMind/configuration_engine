from __future__ import annotations

from dataclasses import dataclass

from configuration_engine.device_definition import DeviceProperty


@dataclass(frozen=True, slots=True)
class FilterDecision:
    """Decision whether to include a property in a captured profile."""

    property: DeviceProperty
    included: bool
    reason: str
