from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from configuration_engine.adapters.zigbee2mqtt.zigbee2mqtt_backend import (
    Zigbee2MqttBackend,
)
from configuration_engine.backend import Backend
from configuration_engine.configuration import Configuration
from configuration_engine.configuration_loader import ConfigurationLoader
from configuration_engine.mqtt import Zigbee2MqttClient


def create_backend(
    configuration: Configuration,
    configuration_path: Path | None = None,
) -> Backend:
    """Create the configured backend."""

    if configuration.backend.name != "zigbee2mqtt":
        raise ValueError(
            f"Unsupported backend: {configuration.backend.name}",
        )

    client = Zigbee2MqttClient(
        host=configuration.mqtt.host,
        port=configuration.mqtt.port,
        username=configuration.mqtt.username,
        password=configuration.mqtt.password,
    )

    client.connect()

    on_mqtt_get_property_discovered: Callable[[str, str, str], None] | None = None

    if configuration_path is not None:

        def persist_mqtt_get_property(
            vendor: str,
            model: str,
            property_name: str,
        ) -> None:
            ConfigurationLoader.update_mqtt_get_property(
                configuration_path,
                vendor,
                model,
                property_name,
            )

        on_mqtt_get_property_discovered = persist_mqtt_get_property

    return Zigbee2MqttBackend(
        client,
        configuration.mqtt_get_properties,
        on_mqtt_get_property_discovered,
    )
