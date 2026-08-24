from __future__ import annotations

from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.profile import Profile


def test_profile_from_snapshot() -> None:
    snapshot = DeviceSnapshot(
        backend="zigbee2mqtt",
        device_id="office",
        model="VZM31-SN",
        values={
            "minimumLevel": 40,
            "maximumLevel": 255,
        },
    )

    profile = Profile.from_snapshot(snapshot)

    assert profile.model == "VZM31-SN"
    assert profile.values == snapshot.values

    assert profile is not snapshot


def test_compare_profiles() -> None:
    current = Profile(
        vendor="Inovelli",
        model="VZM31-SN",
        values={
            "minimumLevel": 20,
            "maximumLevel": 255,
            "deviceOnlyProperty": 123,
        },
    )

    desired = Profile(
        vendor="Inovelli",
        model="VZM31-SN",
        values={
            "minimumLevel": 40,
            "maximumLevel": 255,
        },
    )

    difference = current.compare(desired)

    assert not difference.is_empty
    assert len(difference.differences) == 1

    property_difference = difference.differences[0]

    assert property_difference.property_name == "minimumLevel"
    assert property_difference.current_value == 20
    assert property_difference.desired_value == 40
