from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeviceProperty:
    """Metadata describing a single exposed device property."""

    name: str
    label: str
    property: str
    property_type: str
    access: int | None
    category: str | None
    description: str | None
    unit: str | None
    values: list[str]


@dataclass(frozen=True, slots=True)
class DeviceDefinition:
    """Metadata describing a Zigbee device."""

    description: str
    vendor: str
    model: str
    version: str
    supports_ota: bool

    properties: list[DeviceProperty]
