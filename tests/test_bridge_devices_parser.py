import json

from configuration_engine.adapters.zigbee2mqtt.bridge_devices_parser import (
    BridgeDevicesParser,
)


def test_parse_bridge_devices() -> None:
    parser = BridgeDevicesParser()

    payload = json.dumps(
        [
            {
                "type": "EndDevice",
                "friendly_name": "Zebra",
                "ieee_address": "0x222",
                "manufacturer": "Vendor B",
                "model_id": "Model B",
                "software_build_id": "2.0",
            },
            {
                "type": "Coordinator",
                "friendly_name": "Coordinator",
                "ieee_address": "0x000",
                "manufacturer": "Coordinator Vendor",
                "model_id": "Coordinator Model",
                "software_build_id": "1.0",
            },
            {
                "type": "Router",
                "friendly_name": "alpha",
                "ieee_address": "0x111",
                "manufacturer": "Vendor A",
                "model_id": "Model A",
            },
        ]
    )

    devices = parser.parse(payload)

    assert len(devices) == 2

    assert devices[0].friendly_name == "alpha"
    assert devices[0].ieee_address == "0x111"
    assert devices[0].manufacturer == "Vendor A"
    assert devices[0].model_id == "Model A"
    assert devices[0].firmware is None

    assert devices[1].friendly_name == "Zebra"
    assert devices[1].ieee_address == "0x222"
    assert devices[1].manufacturer == "Vendor B"
    assert devices[1].model_id == "Model B"
    assert devices[1].firmware == "2.0"
