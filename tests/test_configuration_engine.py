from __future__ import annotations

import pytest

from configuration_engine.backend_configuration import BackendConfiguration
from configuration_engine.configuration import Configuration
from configuration_engine.configuration_engine import ConfigurationEngine
from configuration_engine.device_info import DeviceInfo
from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.device_summary import DeviceSummary
from configuration_engine.mqtt_configuration import MqttConfiguration


class FakeBackend:
    def __init__(self, device_lists: list[list[DeviceSummary]]) -> None:
        self._device_lists = iter(device_lists)
        self.device_calls = 0
        self.snapshot_calls: list[str] = []
        self.snapshot_vendors: list[str | None] = []

    def devices(self, timeout: float = 45.0) -> list[DeviceSummary]:
        del timeout
        self.device_calls += 1
        return next(self._device_lists)

    def info(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceInfo:
        del timeout
        return DeviceInfo(
            friendly_name=device,
            ieee_address="0x1234",
            manufacturer="Test",
            model_id="TEST",
            firmware="1.0",
            network_address=1234,
            power_source="Mains (single phase)",
            type="Router",
            supported=True,
            interview_state="SUCCESSFUL",
        )

    def snapshot(
        self,
        device_id: str,
        timeout: float = 45.0,
        vendor: str | None = None,
    ) -> DeviceSnapshot:
        del timeout
        self.snapshot_calls.append(device_id)
        self.snapshot_vendors.append(vendor)
        return DeviceSnapshot(
            backend="zigbee2mqtt",
            device_id=device_id,
            model=None,
            values={},
        )


def _device(name: str) -> DeviceSummary:
    return DeviceSummary(
        friendly_name=name,
        ieee_address="0x1234",
        manufacturer="Test",
        model_id="TEST",
        firmware=None,
    )


def test_from_configuration_rejects_unsupported_backend() -> None:
    configuration = Configuration(
        backend=BackendConfiguration(
            name="unsupported",
        ),
        mqtt=MqttConfiguration(
            host="localhost",
        ),
    )

    with pytest.raises(
        ValueError,
        match=r"Unsupported backend: unsupported",
    ):
        ConfigurationEngine.from_configuration(configuration)


def test_snapshot_uses_current_device_inventory() -> None:
    backend = FakeBackend([[_device("Theater Front")]])
    engine = ConfigurationEngine(backend)

    snapshot = engine.snapshot("Theater Front")
    snapshot = engine.snapshot("Theater Front")

    assert snapshot.device_id == "Theater Front"
    assert backend.device_calls == 1
    assert backend.snapshot_calls == [
        "Theater Front",
        "Theater Front",
    ]
    assert backend.snapshot_vendors == [
        "Test",
        "Test",
    ]


def test_info_returns_device_information() -> None:
    backend = FakeBackend([[_device("Theater Front")]])
    engine = ConfigurationEngine(backend)

    info = engine.info("Theater Front")

    assert info.friendly_name == "Theater Front"
    assert info.ieee_address == "0x1234"
    assert info.manufacturer == "Test"
    assert info.model_id == "TEST"
    assert info.firmware == "1.0"
    assert info.network_address == 1234
    assert info.power_source == "Mains (single phase)"
    assert info.type == "Router"
    assert info.supported is True
    assert info.interview_state == "SUCCESSFUL"


def test_snapshot_refreshes_inventory_when_device_is_missing() -> None:
    backend = FakeBackend(
        [
            [_device("Theater Back")],
            [_device("Theater Front"), _device("Theater Back")],
        ]
    )
    engine = ConfigurationEngine(backend)

    snapshot = engine.snapshot("Theater Front")

    assert snapshot.device_id == "Theater Front"
    assert backend.device_calls == 2
    assert backend.snapshot_calls == ["Theater Front"]
    assert backend.snapshot_vendors == ["Test"]


def test_snapshot_reports_device_missing_after_refresh() -> None:
    backend = FakeBackend(
        [
            [_device("Theater Back")],
            [_device("Theater Back")],
        ]
    )
    engine = ConfigurationEngine(backend)

    with pytest.raises(
        ValueError,
        match=r'Device "Theater Front" was not found in the Zigbee2MQTT device list\.',
    ):
        engine.snapshot("Theater Front")

    assert backend.device_calls == 2
    assert backend.snapshot_calls == []


def test_devices_refreshes_cached_inventory() -> None:
    backend = FakeBackend(
        [
            [_device("Theater Front")],
            [_device("Theater Back")],
        ]
    )
    engine = ConfigurationEngine(backend)

    first = engine.devices()
    second = engine.devices()

    assert [device.friendly_name for device in first] == ["Theater Front"]
    assert [device.friendly_name for device in second] == ["Theater Back"]
    assert backend.device_calls == 2
