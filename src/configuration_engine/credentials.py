from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MqttCredentials:
    """MQTT authentication credentials."""

    username: str | None = None
    password: str | None = None
