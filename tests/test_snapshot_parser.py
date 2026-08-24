import json

from configuration_engine.adapters.zigbee2mqtt.snapshot_parser import SnapshotParser


def test_parse_snapshot() -> None:
    parser = SnapshotParser()

    payload = json.dumps(
        {
            "minimumLevel": 40,
            "maximumLevel": 255,
            "state": "ON",
            "brightness": 74,
        }
    )

    snapshot = parser.parse(
        device_id="0x123456789abcdef",
        payload=payload,
    )

    assert snapshot.backend == "zigbee2mqtt"
    assert snapshot.device_id == "0x123456789abcdef"
    assert snapshot.model is None

    assert snapshot.values["minimumLevel"] == 40
    assert snapshot.values["maximumLevel"] == 255
    assert snapshot.values["brightness"] == 74
    assert snapshot.values["state"] == "ON"
