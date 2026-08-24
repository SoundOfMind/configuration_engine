from __future__ import annotations

from configuration_engine.configuration_engine import ConfigurationEngine
from configuration_engine.device_definition import DeviceDefinition, DeviceProperty
from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.device_summary import DeviceSummary
from configuration_engine.profile import Profile
from configuration_engine.profile_applier import ProfileApplier


class FakeBackend:
    def __init__(self) -> None:
        self.set_calls: list[tuple[str, str, object]] = []
        self.test_property = "old"

    def snapshot(
        self,
        device_id: str,
        timeout: float = 45.0,
        vendor: str | None = None,
    ) -> DeviceSnapshot:
        del vendor
        return DeviceSnapshot(
            backend="test",
            device_id=device_id,
            model="TestModel",
            values={"testProperty": self.test_property},
        )

    def devices(self, timeout: float = 45.0) -> list[DeviceSummary]:
        return [
            DeviceSummary(
                friendly_name="test-device",
                ieee_address="test-ieee-address",
                manufacturer="Test",
                model_id="TestModel",
                firmware=None,
            ),
        ]

    def definition(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceDefinition:
        return DeviceDefinition(
            description="Test device",
            vendor="Test",
            model="TestModel",
            version="1",
            supports_ota=False,
            properties=[
                DeviceProperty(
                    name="testProperty",
                    property="testProperty",
                    label="Test Property",
                    property_type="enum",
                    access=5,
                    category="config",
                    description="Test configuration property.",
                    unit=None,
                    values=["old", "new"],
                ),
            ],
        )

    def set_property(
        self,
        device: str,
        property_name: str,
        value: object,
        timeout: float = 45.0,
    ) -> None:
        self.set_calls.append((device, property_name, value))

        if property_name == "testProperty":
            self.test_property = value


class NonUpdatingBackend(FakeBackend):
    def set_property(
        self,
        device: str,
        property_name: str,
        value: object,
        timeout: float = 45.0,
    ) -> None:
        self.set_calls.append((device, property_name, value))


def test_apply_does_not_write_non_applicable_property() -> None:
    backend = FakeBackend()
    engine = ConfigurationEngine(backend)

    profile = Profile(
        vendor="Test",
        model="TestModel",
        values={"dimmingMode": "Trailing Edge"},
    )

    engine.apply("test-device", profile)

    assert backend.set_calls == []


def test_apply_returns_applied_differences() -> None:
    backend = FakeBackend()
    engine = ConfigurationEngine(backend)

    profile = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "new"},
    )

    difference = engine.apply("test-device", profile)

    assert backend.set_calls == [
        ("test-device", "testProperty", "new"),
    ]

    assert len(difference.differences) == 1

    item = difference.differences[0]

    assert item.property_name == "testProperty"
    assert item.current_value == "old"
    assert item.desired_value == "new"


def test_apply_rejects_vendor_mismatch_without_writing() -> None:
    backend = FakeBackend()
    engine = ConfigurationEngine(backend)

    profile = Profile(
        vendor="WrongVendor",
        model="TestModel",
        values={
            "dimmingMode": "Trailing Edge",
        },
    )

    try:
        engine.apply("test-device", profile)
    except ValueError as exc:
        assert "vendor mismatch" in str(exc)
    else:
        raise AssertionError("Expected vendor mismatch to raise ValueError.")

    assert backend.set_calls == []


def test_apply_rejects_model_mismatch_without_writing() -> None:
    backend = FakeBackend()
    engine = ConfigurationEngine(backend)

    profile = Profile(
        vendor="Test",
        model="WrongModel",
        values={
            "dimmingMode": "Trailing Edge",
        },
    )

    try:
        engine.apply("test-device", profile)
    except ValueError as exc:
        assert "model mismatch" in str(exc)
    else:
        raise AssertionError("Expected model mismatch to raise ValueError.")

    assert backend.set_calls == []


def test_apply_rejects_profile_with_unknown_vendor() -> None:
    backend = FakeBackend()
    engine = ConfigurationEngine(backend)

    profile = Profile(
        vendor=None,
        model="TestModel",
        values={
            "dimmingMode": "Trailing Edge",
        },
    )

    try:
        engine.apply("test-device", profile)
    except ValueError as exc:
        assert "vendor is unknown" in str(exc)
    else:
        raise AssertionError("Expected unknown vendor to raise ValueError.")

    assert backend.set_calls == []


def test_apply_rejects_profile_with_unknown_model() -> None:
    backend = FakeBackend()
    engine = ConfigurationEngine(backend)

    profile = Profile(
        vendor="Test",
        model=None,
        values={
            "dimmingMode": "Trailing Edge",
        },
    )

    try:
        engine.apply("test-device", profile)
    except ValueError as exc:
        assert "model is unknown" in str(exc)
    else:
        raise AssertionError("Expected unknown model to raise ValueError.")

    assert backend.set_calls == []


def test_profile_applier_does_not_write_when_profiles_match() -> None:
    backend = FakeBackend()
    applier = ProfileApplier(backend)

    current = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "old"},
    )

    desired = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "old"},
    )

    difference = applier.apply(
        "test-device",
        current,
        desired,
        timeout=45.0,
    )

    assert difference.is_empty
    assert backend.set_calls == []


def test_profile_applier_writes_and_verifies_changes() -> None:
    backend = FakeBackend()
    applier = ProfileApplier(backend)

    current = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "old"},
    )

    desired = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "new"},
    )

    difference = applier.apply(
        "test-device",
        current,
        desired,
        timeout=45.0,
    )

    assert backend.set_calls == [
        ("test-device", "testProperty", "new"),
    ]

    assert len(difference.differences) == 1

    item = difference.differences[0]

    assert item.property_name == "testProperty"
    assert item.current_value == "old"
    assert item.desired_value == "new"


def test_profile_applier_retries_until_change_is_visible() -> None:
    backend = FakeBackend()
    applier = ProfileApplier(backend)

    original_snapshot = backend.snapshot

    snapshot_calls = 0

    def delayed_snapshot(
        device_id: str,
        timeout: float = 45.0,
        vendor: str | None = None,
    ) -> DeviceSnapshot:
        nonlocal snapshot_calls

        snapshot_calls += 1

        snapshot = original_snapshot(
            device_id,
            timeout,
            vendor,
        )

        if snapshot_calls == 1:
            return DeviceSnapshot(
                backend=snapshot.backend,
                device_id=snapshot.device_id,
                model=snapshot.model,
                values={"testProperty": "old"},
            )

        return snapshot

    backend.snapshot = delayed_snapshot  # type: ignore[method-assign]

    current = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "old"},
    )

    desired = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "new"},
    )

    difference = applier.apply(
        "test-device",
        current,
        desired,
        timeout=45.0,
    )

    assert snapshot_calls == 2
    assert backend.set_calls == [
        ("test-device", "testProperty", "new"),
    ]

    assert len(difference.differences) == 1


def test_profile_applier_returns_remaining_changes_on_timeout(
    monkeypatch,
) -> None:
    backend = NonUpdatingBackend()
    applier = ProfileApplier(backend)

    current = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "old"},
    )

    desired = Profile(
        vendor="Test",
        model="TestModel",
        values={"testProperty": "new"},
    )

    current_time = 0.0

    def fake_monotonic() -> float:
        return current_time

    def fake_sleep(seconds: float) -> None:
        nonlocal current_time
        current_time += seconds

    monkeypatch.setattr(
        "configuration_engine.profile_applier.time.monotonic",
        fake_monotonic,
    )
    monkeypatch.setattr(
        "configuration_engine.profile_applier.time.sleep",
        fake_sleep,
    )

    difference = applier.apply(
        "test-device",
        current,
        desired,
        timeout=2.0,
    )

    assert backend.set_calls == [
        ("test-device", "testProperty", "new"),
    ]

    assert len(difference.differences) == 1

    item = difference.differences[0]

    assert item.property_name == "testProperty"
    assert item.current_value == "old"
    assert item.desired_value == "new"
