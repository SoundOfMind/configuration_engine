from __future__ import annotations

import pytest

from configuration_engine.adapters.zigbee2mqtt.zigbee2mqtt_backend import (
    Zigbee2MqttBackend,
)
from configuration_engine.device_definition import DeviceDefinition, DeviceProperty
from configuration_engine.rules.recommendation_rule import ACCESS_READ


def test_mqtt_get_candidates_use_preferred_order() -> None:
    backend = Zigbee2MqttBackend(
        client=None,
        mqtt_get_properties={},
    )

    definition = DeviceDefinition(
        description="Test device",
        vendor="Test",
        model="TestModel",
        version="1",
        supports_ota=False,
        properties=[
            DeviceProperty(
                name="power",
                property="power",
                label="Power",
                property_type="binary",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
            DeviceProperty(
                name="custom",
                property="custom",
                label="Custom",
                property_type="numeric",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
            DeviceProperty(
                name="linkquality",
                property="linkquality",
                label="Link Quality",
                property_type="numeric",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
            DeviceProperty(
                name="brightness",
                property="brightness",
                label="Brightness",
                property_type="numeric",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
            DeviceProperty(
                name="state",
                property="state",
                label="State",
                property_type="binary",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
        ],
    )

    candidates = backend._mqtt_get_candidates(definition)

    assert candidates == [
        "state",
        "brightness",
        "power",
        "custom",
        "linkquality",
    ]


def test_snapshot_uses_configured_mqtt_get_property() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.requests: list[tuple[str, str, str, float]] = []

        def request(
            self,
            request_topic: str,
            response_topic: str,
            payload: str,
            timeout: float = 5.0,
        ) -> bytes:
            self.requests.append(
                (
                    request_topic,
                    response_topic,
                    payload,
                    timeout,
                )
            )

            return b'{"levelConfigOnLevel":74}'

    client = FakeClient()

    backend = Zigbee2MqttBackend(
        client=client,
        mqtt_get_properties={
            "Test": {
                "TestModel": "levelConfigOnLevel",
            },
        },
    )

    definition = DeviceDefinition(
        description="Test device",
        vendor="Test",
        model="TestModel",
        version="1",
        supports_ota=False,
        properties=[
            DeviceProperty(
                name="levelConfigOnLevel",
                property="levelConfigOnLevel",
                label="Level",
                property_type="numeric",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
        ],
    )

    backend.definition = lambda device, timeout=45.0: definition

    snapshot = backend.snapshot(
        "test-device",
        timeout=10.0,
    )

    assert snapshot.device_id == "test-device"
    assert snapshot.values["levelConfigOnLevel"] == 74

    assert client.requests == [
        (
            "zigbee2mqtt/test-device/get",
            "zigbee2mqtt/test-device",
            '{"levelConfigOnLevel": ""}',
            10.0,
        ),
    ]


def test_info_returns_device_instance_information() -> None:
    class FakeClient:
        def wait_for_message(
            self,
            topic: str,
            timeout: float = 45.0,
        ) -> bytes:
            assert topic == "zigbee2mqtt/bridge/devices"
            assert timeout == 10.0

            return b"""
            [
                {
                    "friendly_name": "Test3 Plug",
                    "ieee_address": "0x0000000000000001",
                    "interview_completed": true,
                    "interview_state": "SUCCESSFUL",
                    "interviewing": false,
                    "manufacturer": "Third Reality, Inc",
                    "model_id": "3RSP019BZ",
                    "network_address": 30134,
                    "power_source": "Mains (single phase)",
                    "software_build_id": "1.01.01",
                    "supported": true,
                    "type": "Router"
                }
            ]
            """

    backend = Zigbee2MqttBackend(
        client=FakeClient(),
        mqtt_get_properties={},
    )

    info = backend.info(
        "Test3 Plug",
        timeout=10.0,
    )

    assert info.friendly_name == "Test3 Plug"
    assert info.ieee_address == "0x0000000000000001"
    assert info.manufacturer == "Third Reality, Inc"
    assert info.model_id == "3RSP019BZ"
    assert info.firmware == "1.01.01"
    assert info.network_address == 30134
    assert info.power_source == "Mains (single phase)"
    assert info.type == "Router"
    assert info.supported is True
    assert info.interview_state == "SUCCESSFUL"


def test_snapshot_discovers_and_caches_mqtt_get_property() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.requests: list[tuple[str, str, str, float]] = []

        def request(
            self,
            request_topic: str,
            response_topic: str,
            payload: str,
            timeout: float = 5.0,
        ) -> bytes:
            self.requests.append(
                (
                    request_topic,
                    response_topic,
                    payload,
                    timeout,
                )
            )

            if '"state": ""' in payload:
                raise TimeoutError("state did not respond")

            return b'{"brightness":74}'

    discoveries: list[tuple[str, str, str]] = []

    def record_discovery(
        vendor: str,
        model: str,
        property_name: str,
    ) -> None:
        discoveries.append(
            (
                vendor,
                model,
                property_name,
            )
        )

    client = FakeClient()

    backend = Zigbee2MqttBackend(
        client=client,
        mqtt_get_properties={},
        on_mqtt_get_property_discovered=record_discovery,
    )

    definition = DeviceDefinition(
        description="Test device",
        vendor="Test",
        model="TestModel",
        version="1",
        supports_ota=False,
        properties=[
            DeviceProperty(
                name="state",
                property="state",
                label="State",
                property_type="binary",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
            DeviceProperty(
                name="brightness",
                property="brightness",
                label="Brightness",
                property_type="numeric",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
        ],
    )

    backend.definition = lambda device, timeout=45.0: definition

    snapshot = backend.snapshot(
        "test-device",
        timeout=10.0,
    )

    assert snapshot.values["brightness"] == 74

    assert client.requests == [
        (
            "zigbee2mqtt/test-device/get",
            "zigbee2mqtt/test-device",
            '{"state": ""}',
            1.0,
        ),
        (
            "zigbee2mqtt/test-device/get",
            "zigbee2mqtt/test-device",
            '{"brightness": ""}',
            1.0,
        ),
    ]

    assert discoveries == [
        ("Test", "TestModel", "brightness"),
    ]

    assert backend._mqtt_get_properties == {
        "Test": {
            "TestModel": "brightness",
        },
    }


def test_snapshot_raises_when_no_mqtt_get_property_responds() -> None:
    class FakeClient:
        def request(
            self,
            request_topic: str,
            response_topic: str,
            payload: str,
            timeout: float = 5.0,
        ) -> bytes:
            raise TimeoutError("no response")

    backend = Zigbee2MqttBackend(
        client=FakeClient(),
        mqtt_get_properties={},
    )

    definition = DeviceDefinition(
        description="Test device",
        vendor="Test",
        model="TestModel",
        version="1",
        supports_ota=False,
        properties=[
            DeviceProperty(
                name="state",
                property="state",
                label="State",
                property_type="binary",
                access=ACCESS_READ,
                category=None,
                description=None,
                unit=None,
                values=[],
            ),
        ],
    )

    backend.definition = lambda device, timeout=45.0: definition

    with pytest.raises(
        TimeoutError,
        match="No MQTT GET property responded for Test TestModel.",
    ):
        backend.snapshot(
            "test-device",
            timeout=10.0,
        )


def test_devices_returns_parsed_bridge_devices() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.topics: list[tuple[str, float]] = []

        def wait_for_message(
            self,
            topic: str,
            timeout: float = 45.0,
        ) -> bytes:
            self.topics.append(
                (
                    topic,
                    timeout,
                )
            )

            return (
                b'[{"type":"Router","friendly_name":"Test Device",'
                b'"ieee_address":"0x123","manufacturer":"Test Vendor",'
                b'"model_id":"Test Model","software_build_id":"1.0"}]'
            )

    client = FakeClient()

    backend = Zigbee2MqttBackend(
        client=client,
        mqtt_get_properties={},
    )

    devices = backend.devices(
        timeout=12.0,
    )

    assert client.topics == [
        (
            "zigbee2mqtt/bridge/devices",
            12.0,
        ),
    ]

    assert len(devices) == 1
    assert devices[0].friendly_name == "Test Device"
    assert devices[0].ieee_address == "0x123"
    assert devices[0].manufacturer == "Test Vendor"
    assert devices[0].model_id == "Test Model"
    assert devices[0].firmware == "1.0"


def test_definition_returns_parsed_device_definition() -> None:
    class FakeClient:
        def wait_for_message(
            self,
            topic: str,
            timeout: float = 45.0,
        ) -> bytes:
            assert topic == "zigbee2mqtt/bridge/devices"
            assert timeout == 12.0

            return (
                b"["
                b'{"friendly_name":"Test Device","definition":'
                b'{"description":"Test description","vendor":"Test Vendor",'
                b'"model":"Test Model","version":"1",'
                b'"exposes":[{"property":"state","label":"State",'
                b'"type":"binary","access":1}]}'
                b"}"
                b"]"
            )

    backend = Zigbee2MqttBackend(
        client=FakeClient(),
        mqtt_get_properties={},
    )

    definition = backend.definition(
        "Test Device",
        timeout=12.0,
    )

    assert definition.description == "Test description"
    assert definition.vendor == "Test Vendor"
    assert definition.model == "Test Model"
    assert definition.version == "1"

    assert len(definition.properties) == 1
    assert definition.properties[0].name == "state"
    assert definition.properties[0].label == "State"


def test_definition_raises_for_unknown_device() -> None:
    class FakeClient:
        def wait_for_message(
            self,
            topic: str,
            timeout: float = 45.0,
        ) -> bytes:
            return (
                b'[{"friendly_name":"Known Device","definition":'
                b'{"description":"Test","vendor":"Test","model":"TestModel",'
                b'"version":"1","exposes":[]}}]'
            )

    backend = Zigbee2MqttBackend(
        client=FakeClient(),
        mqtt_get_properties={},
    )

    with pytest.raises(
        ValueError,
        match='Unknown device "Missing Device".',
    ):
        backend.definition(
            "Missing Device",
            timeout=12.0,
        )
