from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from configuration_engine.configuration_paths import (
    default_configuration_directory,
    location_file,
)


@dataclass(frozen=True, slots=True)
class MqttSettings:
    """Validated MQTT connection settings."""

    host: str
    port: int
    username: str
    password: str


def validate_mqtt_settings(
    host: str,
    port: str,
    username: str,
    password: str,
) -> MqttSettings:
    """Validate MQTT settings and return them as a typed value."""

    if not host:
        raise ValueError("MQTT host is required.")

    try:
        port_number = int(port)
    except ValueError as exc:
        raise ValueError("MQTT port must be a number.") from exc

    if not 1 <= port_number <= 65535:
        raise ValueError("MQTT port must be between 1 and 65535.")

    if not username:
        raise ValueError("MQTT username is required.")

    if not password:
        raise ValueError("MQTT password is required.")

    return MqttSettings(
        host=host,
        port=port_number,
        username=username,
        password=password,
    )


def write_location_pointer(directory: Path) -> None:
    """Make the selected configuration directory active."""

    pointer = location_file()
    default_directory = default_configuration_directory()

    if directory == default_directory:
        if pointer.exists():
            pointer.unlink()
        return

    pointer.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = pointer.with_suffix(f"{pointer.suffix}.tmp")

    try:
        with temporary.open(
            "w",
            encoding="utf-8",
        ) as file:
            yaml.safe_dump(
                {"configuration_directory": str(directory)},
                file,
                sort_keys=False,
            )

        temporary.replace(pointer)

    finally:
        if temporary.exists():
            temporary.unlink()
