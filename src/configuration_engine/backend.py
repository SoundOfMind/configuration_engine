from __future__ import annotations

from typing import Protocol

from configuration_engine.device_definition import DeviceDefinition
from configuration_engine.device_info import DeviceInfo
from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.device_summary import DeviceSummary


class Backend(Protocol):
    """Contract implemented by configuration backends."""

    def snapshot(
        self,
        device_id: str,
        timeout: float = 45.0,
        vendor: str | None = None,
    ) -> DeviceSnapshot: ...

    def devices(
        self,
        timeout: float = 45.0,
    ) -> list[DeviceSummary]: ...

    def info(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceInfo: ...

    def definition(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceDefinition: ...

    def set_property(
        self,
        device: str,
        property_name: str,
        value: object,
        timeout: float = 45.0,
    ) -> None: ...
