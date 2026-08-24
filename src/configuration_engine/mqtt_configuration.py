from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MqttConfiguration:
    """MQTT connection settings."""

    host: str
    port: int = 1883
    username: str | None = None
    password: str | None = None
