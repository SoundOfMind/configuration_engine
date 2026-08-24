from __future__ import annotations

from configuration_engine.adapters.zigbee2mqtt.device_definition_parser import (
    DeviceDefinitionParser,
)
from configuration_engine.rules.recommendation_rule import ACCESS_READ_WRITE


def test_parse_uses_backend_property_name() -> None:
    parser = DeviceDefinitionParser()

    definition = {
        "exposes": [
            {
                "features": [
                    {
                        "name": "state",
                        "property": "fan_state",
                        "label": "State",
                        "type": "binary",
                        "access": ACCESS_READ_WRITE,
                    }
                ]
            }
        ]
    }

    result = parser.parse(definition)

    assert result.properties[0].name == "fan_state"
    assert result.properties[0].label == "State"
