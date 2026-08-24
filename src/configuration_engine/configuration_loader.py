from __future__ import annotations

import os
import stat
import tempfile
import types
from pathlib import Path
from typing import Any, Self

import yaml

from configuration_engine.backend_configuration import BackendConfiguration
from configuration_engine.configuration import Configuration
from configuration_engine.mqtt_configuration import MqttConfiguration


class _FileLock:
    """Cross-platform exclusive lock backed by a separate lock file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stream: Any = None

    def __enter__(self) -> Self:
        self._stream = self._path.open("a+b")

        if self._stream.seek(0, os.SEEK_END) == 0:
            self._stream.write(b"\0")
            self._stream.flush()

        self._stream.seek(0)

        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(  # type: ignore[attr-defined]
                self._stream.fileno(),
                fcntl.LOCK_EX,  # type: ignore[attr-defined]
            )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:

        del exc_type, exc_value, traceback

        assert self._stream is not None

        if os.name == "nt":
            import msvcrt

            self._stream.seek(0)
            msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(  # type: ignore[attr-defined]
                self._stream.fileno(),
                fcntl.LOCK_UN,  # type: ignore[attr-defined]
            )

        self._stream.close()
        self._stream = None


class ConfigurationLoader:
    """Loads and persists application configuration."""

    @staticmethod
    def load(path: str | Path) -> Configuration:
        """Load application configuration."""

        document = ConfigurationLoader._read_document(Path(path))
        return ConfigurationLoader._from_document(document)

    @staticmethod
    def create(
        path: str | Path,
        configuration: Configuration,
    ) -> None:
        """Create a new application configuration."""

        configuration_path = Path(path)

        if configuration_path.exists():
            raise FileExistsError(configuration_path)

        configuration_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        document = ConfigurationLoader._to_document(configuration)

        with _FileLock(
            ConfigurationLoader._lock_path(configuration_path),
        ):
            if configuration_path.exists():
                raise FileExistsError(configuration_path)

            ConfigurationLoader._write_document(
                configuration_path,
                document,
            )

    @staticmethod
    def save(
        path: str | Path,
        configuration: Configuration,
    ) -> None:
        """Persist application configuration as an atomic, protected write."""

        configuration_path = Path(path)
        ConfigurationLoader._require_read_only(configuration_path)

        document = ConfigurationLoader._to_document(configuration)

        with _FileLock(ConfigurationLoader._lock_path(configuration_path)):
            ConfigurationLoader._require_read_only(configuration_path)
            current_document = ConfigurationLoader._read_document(configuration_path)
            ConfigurationLoader._validate_document(current_document)

            ConfigurationLoader._write_backup(configuration_path)
            ConfigurationLoader._write_document(configuration_path, document)

    @staticmethod
    def update_mqtt_get_property(
        path: str | Path,
        vendor: str,
        model: str,
        property_name: str,
    ) -> bool:
        """Persist a newly discovered MQTT GET property.

        Returns True when the configuration file was changed and False when the
        requested mapping was already present with the same value.
        """

        configuration_path = Path(path)
        ConfigurationLoader._require_read_only(configuration_path)

        with _FileLock(ConfigurationLoader._lock_path(configuration_path)):
            ConfigurationLoader._require_read_only(configuration_path)
            document = ConfigurationLoader._read_document(configuration_path)
            ConfigurationLoader._validate_document(document)

            properties = document.setdefault("mqtt_get_properties", {})
            if not isinstance(properties, dict):
                raise TypeError("'mqtt_get_properties' must be a mapping.")

            vendor_properties = properties.setdefault(vendor, {})
            if not isinstance(vendor_properties, dict):
                raise TypeError(f"MQTT GET properties for vendor {vendor!r} must be a mapping.")

            current = vendor_properties.get(model)
            if current == property_name:
                return False

            ConfigurationLoader._write_backup(configuration_path)

            vendor_properties[model] = property_name
            ConfigurationLoader._write_document(configuration_path, document)

            return True

    @staticmethod
    def _read_document(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)

        if not isinstance(document, dict):
            raise TypeError("Configuration document must be a YAML mapping.")

        return document

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Configuration:
        ConfigurationLoader._validate_document(document)

        backend = document["backend"]
        mqtt = document["mqtt"]

        defaults = document.get("defaults", {})
        mqtt_get_properties = document.get("mqtt_get_properties", {})

        if not isinstance(defaults, dict):
            raise TypeError("'defaults' must be a mapping.")
        if not isinstance(mqtt_get_properties, dict):
            raise TypeError("'mqtt_get_properties' must be a mapping.")

        return Configuration(
            backend=BackendConfiguration(
                name=backend["name"],
            ),
            mqtt=MqttConfiguration(
                host=mqtt["host"],
                port=mqtt.get("port", 1883),
                username=mqtt.get("username"),
                password=mqtt.get("password"),
            ),
            mqtt_get_properties=mqtt_get_properties,
            timeout=defaults.get("timeout", 45.0),
        )

    @staticmethod
    def _to_document(configuration: Configuration) -> dict[str, Any]:
        return {
            "backend": {
                "name": configuration.backend.name,
            },
            "mqtt": {
                "host": configuration.mqtt.host,
                "port": configuration.mqtt.port,
            },
            "defaults": {
                "timeout": configuration.timeout,
            },
            "mqtt_get_properties": configuration.mqtt_get_properties,
        }

    @staticmethod
    def _validate_document(document: dict[str, Any]) -> None:
        backend = document.get("backend")
        mqtt = document.get("mqtt")

        if not isinstance(backend, dict) or "name" not in backend:
            raise ValueError("Configuration is missing 'backend.name'.")
        if not isinstance(mqtt, dict) or "host" not in mqtt:
            raise ValueError("Configuration is missing 'mqtt.host'.")

    @staticmethod
    def _lock_path(path: Path) -> Path:
        return path.with_name(f"{path.name}.lock")

    @staticmethod
    def _backup_path(path: Path) -> Path:
        return path.with_name(f"{path.name}.bak")

    @staticmethod
    def _require_read_only(path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)

        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o222:
            raise PermissionError(
                f"Configuration file must be read-only before persistence: {path}"
            )

    @staticmethod
    def _make_read_only(path: Path) -> None:
        current_mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(current_mode & ~0o222)

        ConfigurationLoader._require_read_only(path)

    @staticmethod
    def _make_writable(path: Path) -> None:
        current_mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(current_mode | stat.S_IWUSR)

    @staticmethod
    def _replace(path: Path, replacement: Path) -> None:
        """Atomically replace path, handling a read-only Windows destination."""

        try:
            os.replace(replacement, path)
        except PermissionError:
            # Windows may reject replacing a read-only destination. The old
            # file is protected by the lock, so temporarily clear its write
            # protection only for the atomic replacement.
            ConfigurationLoader._make_writable(path)
            os.replace(replacement, path)

    @staticmethod
    def _write_backup(path: Path) -> None:
        backup = ConfigurationLoader._backup_path(path)
        temporary = ConfigurationLoader._temporary_path(path, "backup")

        try:
            with path.open("rb") as source, temporary.open("wb") as destination:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())

            ConfigurationLoader._make_read_only(temporary)
            ConfigurationLoader._replace(backup, temporary)
            ConfigurationLoader._make_read_only(backup)
        finally:
            if temporary.exists():
                temporary.unlink()

    @staticmethod
    def _write_document(path: Path, document: dict[str, Any]) -> None:
        temporary = ConfigurationLoader._temporary_path(path, "config")

        try:
            with temporary.open("w", encoding="utf-8", newline="") as stream:
                yaml.safe_dump(
                    document,
                    stream,
                    sort_keys=False,
                )
                stream.flush()
                os.fsync(stream.fileno())

            # Validate the exact YAML bytes that are about to be installed.
            written_document = ConfigurationLoader._read_document(temporary)
            ConfigurationLoader._validate_document(written_document)

            # The installed file must be read-only from the moment it becomes
            # the canonical configuration file.
            ConfigurationLoader._make_read_only(temporary)
            ConfigurationLoader._replace(path, temporary)
            ConfigurationLoader._make_read_only(path)
        finally:
            if temporary.exists():
                temporary.unlink()

        ConfigurationLoader._require_read_only(path)

    @staticmethod
    def _temporary_path(path: Path, purpose: str) -> Path:
        file_descriptor, name = tempfile.mkstemp(
            prefix=f".{path.name}.{purpose}.",
            suffix=".tmp",
            dir=path.parent,
        )
        os.close(file_descriptor)
        return Path(name)
