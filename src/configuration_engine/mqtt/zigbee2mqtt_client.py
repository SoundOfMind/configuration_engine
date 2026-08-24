from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTT_ERR_SUCCESS, Client, MQTTMessage


class Zigbee2MqttClient:
    """Thin wrapper around the paho-mqtt client."""

    def __init__(
        self,
        host: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._client = Client(
            mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
        )

        if username is not None:
            self._client.username_pw_set(username, password)

        self._host = host
        self._port = port

        self._connected = threading.Event()

        self._handlers: dict[str, Callable[[bytes], None]] = {}

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def connect(self, timeout: float = 5.0) -> None:
        self._client.connect(self._host, self._port)
        self._client.loop_start()

        if not self._connected.wait(timeout):
            raise TimeoutError("Timed out waiting for MQTT connection.")

    def disconnect(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()

    def publish(
        self,
        topic: str,
        payload: str,
        retain: bool = False,
    ) -> None:
        if not self.is_connected:
            raise RuntimeError("MQTT client is not connected.")

        result = self._client.publish(
            topic=topic,
            payload=payload,
            retain=retain,
        )

        result.wait_for_publish()

        if not result.is_published():
            raise RuntimeError(f"Failed to publish to topic '{topic}'.")

    def subscribe(
        self,
        topic: str,
        handler: Callable[[bytes], None],
    ) -> None:
        if not self.is_connected:
            raise RuntimeError("MQTT client is not connected.")

        self._handlers[topic] = handler

        result, _ = self._client.subscribe(topic)

        if result != MQTT_ERR_SUCCESS:
            self._handlers.pop(topic, None)
            raise RuntimeError(f"Failed to subscribe to topic '{topic}'.")

    def unsubscribe(
        self,
        topic: str,
    ) -> None:
        if not self.is_connected:
            raise RuntimeError("MQTT client is not connected.")

        result, _ = self._client.unsubscribe(topic)

        if result != MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Failed to unsubscribe from topic '{topic}'.")

        self._handlers.pop(topic, None)

    def _device_topic(
        self,
        device: str,
    ) -> str:
        """Return the MQTT topic for a device."""

        return f"zigbee2mqtt/{device}"

    def set_property(
        self,
        device: str,
        property_name: str,
        value: object,
        timeout: float = 45.0,
    ) -> None:
        """Set a property on a Zigbee2MQTT device."""

        topic = f"{self._device_topic(device)}/set"

        payload = json.dumps(
            {
                property_name: value,
            }
        )

        self.publish(
            topic=topic,
            payload=payload,
        )

    def _on_connect(
        self,
        client: Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del client, userdata, flags, properties

        if reason_code == 0:
            self._connected.set()

    def _on_disconnect(
        self,
        client: Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del client, userdata, flags, reason_code, properties

        self._connected.clear()

    @property
    def is_connected(self) -> bool:
        """Return True if the MQTT client is connected."""

        return self._connected.is_set()

    def _on_message(
        self,
        client: Client,
        userdata: Any,
        message: MQTTMessage,
    ) -> None:
        del client, userdata

        handler = self._handlers.get(message.topic)

        if handler is not None:
            handler(message.payload)

    def wait_for_message(
        self,
        topic: str,
        timeout: float = 45.0,
    ) -> bytes:
        if not self.is_connected:
            raise RuntimeError("MQTT client is not connected.")

        event = threading.Event()
        payload: bytes | None = None

        def handler(message: bytes) -> None:
            nonlocal payload
            payload = message
            event.set()

        self.subscribe(topic, handler)

        try:
            if not event.wait(timeout):
                raise TimeoutError(f"Timed out waiting for '{topic}'.")

            assert payload is not None
            return payload

        finally:
            self.unsubscribe(topic)

    def request(
        self,
        request_topic: str,
        response_topic: str,
        payload: str,
        timeout: float = 5.0,
    ) -> bytes:
        if not self.is_connected:
            raise RuntimeError("MQTT client is not connected.")

        event = threading.Event()
        response: bytes | None = None

        def handler(message: bytes) -> None:
            nonlocal response
            response = message
            event.set()

        self.subscribe(response_topic, handler)

        try:
            self.publish(request_topic, payload)

            if not event.wait(timeout):
                raise TimeoutError(f"Timed out waiting for '{response_topic}'.")

            assert response is not None
            return response

        finally:
            self.unsubscribe(response_topic)
