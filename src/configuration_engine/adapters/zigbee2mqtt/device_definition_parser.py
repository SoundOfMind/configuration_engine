from __future__ import annotations

from typing import Any, cast

from configuration_engine.device_definition import (
    DeviceDefinition,
    DeviceProperty,
)


class DeviceDefinitionParser:
    """Parse a Zigbee2MQTT device definition."""

    def parse(
        self,
        definition: dict[str, Any],
    ) -> DeviceDefinition:

        properties: list[DeviceProperty] = []

        for expose in cast(list[dict[str, Any]], definition.get("exposes", [])):
            self._collect(
                expose,
                properties,
            )

        return DeviceDefinition(
            description=str(definition.get("description", "")),
            vendor=str(definition.get("vendor", "")),
            model=str(definition.get("model", "")),
            version=str(definition.get("version", "")),
            supports_ota=bool(definition.get("supports_ota", False)),
            properties=properties,
        )

    def _collect(
        self,
        expose: dict[str, Any],
        properties: list[DeviceProperty],
    ) -> None:

        features = expose.get("features")

        if isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict):
                    self._collect(
                        feature,
                        properties,
                    )
            return

        name = expose.get("property", expose.get("name"))

        if not isinstance(name, str):
            return

        values = expose.get("values")

        properties.append(
            DeviceProperty(
                name=name,
                property=str(expose.get("property", name)),
                label=str(expose.get("label", name)),
                property_type=str(expose.get("type", "")),
                access=cast(int | None, expose.get("access")),
                category=cast(str | None, expose.get("category")),
                description=cast(str | None, expose.get("description")),
                unit=cast(str | None, expose.get("unit")),
                values=list(values) if isinstance(values, list) else [],
            )
        )
