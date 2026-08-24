from __future__ import annotations

from configuration_engine.backend_configuration import BackendConfiguration
from configuration_engine.configuration import Configuration
from configuration_engine.mqtt_configuration import MqttConfiguration


def test_configuration_defaults_are_applied() -> None:
    config = Configuration(
        backend=BackendConfiguration(
            name="zigbee2mqtt",
        ),
        mqtt=MqttConfiguration(
            host="192.168.1.24",
        ),
    )

    assert config.backend.name == "zigbee2mqtt"

    assert config.mqtt.host == "192.168.1.24"
    assert config.mqtt.port == 1883
    assert config.mqtt.username is None
    assert config.mqtt.password is None

    assert config.timeout == 45.0
