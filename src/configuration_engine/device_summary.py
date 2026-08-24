from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeviceSummary:
    """Summary information describing a Zigbee device."""

    friendly_name: str
    ieee_address: str
    manufacturer: str
    model_id: str
    firmware: str | None
