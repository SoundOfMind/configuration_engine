from __future__ import annotations

from dataclasses import dataclass, field

from configuration_engine.backend_configuration import BackendConfiguration
from configuration_engine.mqtt_configuration import MqttConfiguration


@dataclass(frozen=True, slots=True)
class Configuration:
    """Application configuration."""

    backend: BackendConfiguration
    mqtt: MqttConfiguration
    mqtt_get_properties: dict[str, dict[str, str]] = field(default_factory=dict)
    timeout: float = 45.0
