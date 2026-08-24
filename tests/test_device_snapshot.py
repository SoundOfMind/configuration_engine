from configuration_engine.device_snapshot import DeviceSnapshot


def test_snapshot_stores_values() -> None:
    snapshot = DeviceSnapshot(
        backend="zigbee2mqtt",
        device_id="0x1234",
        model="VZM31-SN",
        values={
            "minimumLevel": 40,
            "state": "ON",
        },
    )

    assert snapshot.backend == "zigbee2mqtt"
    assert snapshot.device_id == "0x1234"
    assert snapshot.values["minimumLevel"] == 40
    assert snapshot.values["state"] == "ON"
