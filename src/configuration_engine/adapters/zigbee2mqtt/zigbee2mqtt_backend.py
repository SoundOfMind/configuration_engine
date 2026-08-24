from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, cast

from configuration_engine.adapters.zigbee2mqtt.bridge_devices_parser import BridgeDevicesParser
from configuration_engine.adapters.zigbee2mqtt.device_definition_parser import (
    DeviceDefinitionParser,
)
from configuration_engine.backend import Backend
from configuration_engine.device_definition import DeviceDefinition
from configuration_engine.device_info import DeviceInfo
from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.device_summary import DeviceSummary
from configuration_engine.mqtt import Zigbee2MqttClient
from configuration_engine.rules.recommendation_rule import ACCESS_READ

from .snapshot_parser import SnapshotParser


class Zigbee2MqttBackend(Backend):
    """Device adapter for Zigbee2MQTT."""

    def __init__(
        self,
        client: Zigbee2MqttClient,
        mqtt_get_properties: dict[str, dict[str, str]],
        on_mqtt_get_property_discovered: Callable[[str, str, str], None] | None = None,
    ) -> None:
        self._client = client
        self._parser = SnapshotParser()
        self._bridge_devices_parser = BridgeDevicesParser()
        self._mqtt_get_properties = mqtt_get_properties
        self._on_mqtt_get_property_discovered = on_mqtt_get_property_discovered

    def snapshot(
        self,
        device_id: str,
        timeout: float = 45.0,
        vendor: str | None = None,
    ) -> DeviceSnapshot:
        """Return the current state of a Zigbee2MQTT device."""

        topic = f"zigbee2mqtt/{device_id}"

        definition = self.definition(
            device_id,
            timeout,
        )

        canonical_vendor = vendor or definition.vendor

        configured = self._mqtt_get_properties.get(
            canonical_vendor,
            {},
        ).get(definition.model)

        if configured is not None:
            property_name = configured
            payload = self._client.request(
                request_topic=f"{topic}/get",
                response_topic=topic,
                payload=json.dumps({property_name: ""}),
                timeout=timeout,
            )
        else:
            candidates = self._mqtt_get_candidates(definition)
            payload = None
            property_name = None

            for candidate in candidates:
                try:
                    payload = self._client.request(
                        request_topic=f"{topic}/get",
                        response_topic=topic,
                        payload=json.dumps({candidate: ""}),
                        timeout=1.0,
                    )
                    property_name = candidate
                    break
                except TimeoutError:
                    continue

            if payload is None or property_name is None:
                raise TimeoutError(
                    f"No MQTT GET property responded for {definition.vendor} {definition.model}."
                )

            if self._on_mqtt_get_property_discovered is not None:
                self._on_mqtt_get_property_discovered(
                    canonical_vendor,
                    definition.model,
                    property_name,
                )

            self._mqtt_get_properties.setdefault(
                canonical_vendor,
                {},
            )[definition.model] = property_name

        if payload is None:
            raise TimeoutError(f"No MQTT GET response for {definition.vendor} {definition.model}.")

        return self._parser.parse(
            device_id=device_id,
            payload=payload.decode(),
        )

    def set_property(
        self,
        device: str,
        property_name: str,
        value: object,
        timeout: float = 45.0,
    ) -> None:
        """Set a Zigbee2MQTT device property."""

        self._client.set_property(
            device,
            property_name,
            value,
            timeout,
        )

    def devices(
        self,
        timeout: float = 45.0,
    ) -> list[DeviceSummary]:
        """Return the available Zigbee2MQTT devices."""

        payload = self._client.wait_for_message(
            "zigbee2mqtt/bridge/devices",
            timeout,
        )

        return self._bridge_devices_parser.parse(
            payload.decode(),
        )

    def info(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceInfo:
        """Return information about a Zigbee device."""

        payload = self._client.wait_for_message(
            "zigbee2mqtt/bridge/devices",
            timeout,
        )

        device_objects = cast(
            list[dict[str, Any]],
            json.loads(payload),
        )

        for obj in device_objects:
            if obj["friendly_name"] == device:
                return DeviceInfo(
                    friendly_name=obj["friendly_name"],
                    ieee_address=obj["ieee_address"],
                    manufacturer=obj["manufacturer"],
                    model_id=obj["model_id"],
                    firmware=obj.get("software_build_id"),
                    network_address=obj.get("network_address"),
                    power_source=obj.get("power_source"),
                    type=obj.get("type"),
                    supported=obj.get("supported"),
                    interview_state=obj.get("interview_state"),
                )

        raise ValueError(f'Unknown device "{device}".')

    def definition(
        self,
        device: str,
        timeout: float = 45.0,
    ) -> DeviceDefinition:
        """Return the definition for a Zigbee2MQTT device."""

        payload = self._client.wait_for_message(
            "zigbee2mqtt/bridge/devices",
            timeout,
        )

        device_objects = cast(
            list[dict[str, Any]],
            json.loads(payload),
        )

        parser = DeviceDefinitionParser()

        for obj in device_objects:
            if obj["friendly_name"] == device:
                return parser.parse(
                    cast(
                        dict[str, Any],
                        obj["definition"],
                    )
                )

        raise ValueError(f'Unknown device "{device}".')

    def _mqtt_get_candidates(
        self,
        definition: DeviceDefinition,
    ) -> list[str]:
        """Return MQTT GET properties in preferred order."""

        readable = [
            property.name
            for property in definition.properties
            if (property.access is not None and property.access & ACCESS_READ)
        ]

        preferred = [
            "state",
            "brightness",
            "power",
        ]

        candidates = [name for name in preferred if name in readable]

        candidates.extend(
            name for name in readable if name not in candidates and name != "linkquality"
        )

        if "linkquality" in readable:
            candidates.append("linkquality")

        return candidates
