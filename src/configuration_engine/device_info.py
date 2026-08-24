from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Information describing a Zigbee device instance."""

    friendly_name: str
    ieee_address: str
    manufacturer: str
    model_id: str
    firmware: str | None
    network_address: int | None
    power_source: str | None
    type: str | None
    supported: bool | None
    interview_state: str | None
