from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from configuration_engine.analysis import Analysis
from configuration_engine.backend import Backend
from configuration_engine.backend_factory import create_backend
from configuration_engine.configuration import Configuration
from configuration_engine.configuration_loader import ConfigurationLoader
from configuration_engine.configuration_paths import credentials_file
from configuration_engine.credentials_loader import CredentialsLoader
from configuration_engine.device_definition import DeviceDefinition
from configuration_engine.device_info import DeviceInfo
from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.device_summary import DeviceSummary
from configuration_engine.profile import Profile
from configuration_engine.profile_applier import ProfileApplier
from configuration_engine.profile_difference import ProfileDifference
from configuration_engine.profile_filter import ProfileFilter
from configuration_engine.property_filter import PropertyFilter


class ConfigurationEngine:
    """High-level interface to the Configuration Engine."""

    @classmethod
    def from_file(
        cls,
        path: str | Path,
    ) -> ConfigurationEngine:
        """Create an engine from a configuration file."""

        configuration_path = Path(path)
        configuration = ConfigurationLoader.load(configuration_path)

        credentials_path = credentials_file(configuration_path.parent)

        if credentials_path.is_file():
            credentials = CredentialsLoader.load(credentials_path)

            configuration = replace(
                configuration,
                mqtt=replace(
                    configuration.mqtt,
                    username=credentials.username,
                    password=credentials.password,
                ),
            )

        return cls.from_configuration(
            configuration,
            configuration_path=configuration_path,
        )

    @classmethod
    def from_configuration(
        cls,
        configuration: Configuration,
        configuration_path: str | Path | None = None,
    ) -> ConfigurationEngine:
        """Create an engine from an existing Configuration object."""

        backend = create_backend(
            configuration,
            Path(configuration_path) if configuration_path is not None else None,
        )

        return cls(backend)

    def __init__(
        self,
        _backend: Backend,
    ) -> None:
        self._backend = _backend
        self._profile_applier = ProfileApplier(_backend)
        self._devices: list[DeviceSummary] | None = None

    def snapshot(
        self,
        device_id: str,
        timeout: float = 45.0,
    ) -> DeviceSnapshot:
        """Return the current state of a device."""

        device = self._require_device(device_id, timeout)

        return self._backend.snapshot(
            device_id,
            timeout,
            device.manufacturer,
        )

    def capture(
        self,
        device_id: str,
        timeout: float = 45.0,
    ) -> Profile:
        """Capture a device configuration as a profile."""

        snapshot = self.snapshot(
            device_id,
            timeout,
        )

        definition = self.definition(
            device_id,
            timeout,
        )

        values = PropertyFilter().filter(
            definition,
            snapshot,
        )

        filtered_snapshot = DeviceSnapshot(
            backend=snapshot.backend,
            device_id=snapshot.device_id,
            model=snapshot.model,
            values=values,
        )

        return Profile.from_snapshot(
            filtered_snapshot,
            vendor=definition.vendor,
            model=definition.model,
        )

    def compare(
        self,
        device: str,
        profile: Profile,
        timeout: float = 45.0,
    ) -> ProfileDifference:
        """Compare a device with a profile."""

        current = Profile.from_snapshot(
            self.snapshot(
                device,
                timeout,
            )
        )

        return current.compare(profile)

    def apply(
        self,
        device: str,
        profile: Profile,
        timeout: float = 45.0,
        on_progress: Callable[[str], None] | None = None,
    ) -> ProfileDifference:
        """Apply a profile to a device."""

        current = self.capture(
            device,
            timeout,
        )

        definition = self.definition(
            device,
            timeout,
        )

        if profile.vendor is None:
            raise ValueError("Cannot apply profile: profile vendor is unknown.")

        if profile.model is None:
            raise ValueError("Cannot apply profile: profile model is unknown.")

        if profile.vendor != definition.vendor:
            raise ValueError(
                "Cannot apply profile: vendor mismatch: "
                f"profile={profile.vendor!r}, "
                f"device={definition.vendor!r}."
            )

        if profile.model != definition.model:
            raise ValueError(
                "Cannot apply profile: model mismatch: "
                f"profile={profile.model!r}, "
                f"device={definition.model!r}."
            )

        desired = ProfileFilter().filter(
            profile,
            definition,
        )

        return self._profile_applier.apply(
            device,
            current,
            desired,
            timeout,
            on_progress,
        )

    def info(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceInfo:
        """Return information about a device."""

        self._require_device(
            device,
            timeout,
        )

        return self._backend.info(
            device,
            timeout,
        )

    def devices(
        self,
        timeout: float = 45.0,
    ) -> list[DeviceSummary]:
        """Refresh and return the available devices."""

        self._devices = self._backend.devices(timeout)
        return self._devices

    def definition(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceDefinition:
        """Return the metadata for a device."""

        device_summary = self._require_device(
            device,
            timeout,
        )

        return self._backend.definition(
            device_summary.friendly_name,
            timeout,
        )

    def analyze(
        self,
        device_id: str,
        timeout: float = 45.0,
    ) -> Analysis:
        """Analyze a device."""

        definition = self.definition(
            device_id,
            timeout,
        )

        snapshot = self.snapshot(
            device_id,
            timeout,
        )

        recommendations = PropertyFilter().decisions(
            definition,
            snapshot,
        )

        return Analysis(
            device=device_id,
            model=snapshot.model,
            recommendations=recommendations,
        )

    def _require_device(
        self,
        device_id: str,
        timeout: float,
    ) -> DeviceSummary:
        """Return a device from the current inventory, refreshing if necessary."""

        if self._devices is None:
            devices = self.devices(timeout)
        else:
            devices = self._devices

        for device in devices:
            if device.friendly_name == device_id:
                return device

        devices = self.devices(timeout)

        for device in devices:
            if device.friendly_name == device_id:
                return device

        raise ValueError(f'Device "{device_id}" was not found in the Zigbee2MQTT device list.')
