from __future__ import annotations

import threading

import pytest

from configuration_engine.mqtt.zigbee2mqtt_client import Zigbee2MqttClient


class FakePublishResult:
    def wait_for_publish(self) -> None:
        pass

    def is_published(self) -> bool:
        return True


class FakeMqttClient:
    def __init__(self) -> None:
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.subscriptions: list[str] = []
        self.unsubscriptions: list[str] = []
        self.subscribed = threading.Event()
        self.respond_to_publish = True

    def subscribe(
        self,
        topic: str,
    ) -> tuple[int, int]:
        self.subscriptions.append(topic)
        self.subscribed.set()
        return 0, 1

    def unsubscribe(
        self,
        topic: str,
    ) -> tuple[int, int]:
        self.unsubscriptions.append(topic)
        return 0, 1

    def publish(
        self,
        topic: str,
        payload: str,
        retain: bool = False,
    ) -> FakePublishResult:
        self.published_topic = topic
        self.published_payload = payload
        self.published_retain = retain

        if self.respond_to_publish:
            message = type(
                "Message",
                (),
                {
                    "topic": "zigbee2mqtt/test-device",
                    "payload": b'{"state":"ON"}',
                },
            )()

            self.on_message(
                self,
                None,
                message,
            )

        return FakePublishResult()


def test_wait_for_message_receives_payload() -> None:
    client = Zigbee2MqttClient("localhost")

    fake = FakeMqttClient()
    client._client = fake
    client._connected.set()

    def send_message() -> None:
        fake.subscribed.wait()

        message = type(
            "Message",
            (),
            {
                "topic": "zigbee2mqtt/test-device",
                "payload": b'{"state":"ON"}',
            },
        )()

        client._on_message(
            fake,
            None,
            message,
        )

    thread = threading.Thread(target=send_message)
    thread.start()

    payload = client.wait_for_message(
        "zigbee2mqtt/test-device",
        timeout=1.0,
    )

    thread.join()

    assert payload == b'{"state":"ON"}'
    assert fake.subscriptions == ["zigbee2mqtt/test-device"]
    assert fake.unsubscriptions == ["zigbee2mqtt/test-device"]


def test_wait_for_message_unsubscribes_on_timeout() -> None:
    client = Zigbee2MqttClient("localhost")

    fake = FakeMqttClient()
    client._client = fake
    client._connected.set()

    with pytest.raises(
        TimeoutError,
        match="Timed out waiting for 'zigbee2mqtt/test-device'.",
    ):
        client.wait_for_message(
            "zigbee2mqtt/test-device",
            timeout=0.01,
        )

    assert fake.subscriptions == ["zigbee2mqtt/test-device"]
    assert fake.unsubscriptions == ["zigbee2mqtt/test-device"]


def test_request_publishes_and_receives_response() -> None:
    client = Zigbee2MqttClient("localhost")

    fake = FakeMqttClient()
    client._client = fake
    fake.on_message = client._on_message
    client._connected.set()

    response = client.request(
        request_topic="zigbee2mqtt/test-device/get",
        response_topic="zigbee2mqtt/test-device",
        payload='{"state":""}',
        timeout=1.0,
    )

    assert response == b'{"state":"ON"}'
    assert fake.subscriptions == ["zigbee2mqtt/test-device"]
    assert fake.unsubscriptions == ["zigbee2mqtt/test-device"]
    assert fake.published_topic == "zigbee2mqtt/test-device/get"
    assert fake.published_payload == '{"state":""}'
    assert fake.published_retain is False


def test_request_unsubscribes_on_timeout() -> None:
    client = Zigbee2MqttClient("localhost")

    fake = FakeMqttClient()
    fake.respond_to_publish = False
    client._client = fake
    fake.on_message = client._on_message
    client._connected.set()

    with pytest.raises(
        TimeoutError,
        match="Timed out waiting for 'zigbee2mqtt/test-device'.",
    ):
        client.request(
            request_topic="zigbee2mqtt/test-device/get",
            response_topic="zigbee2mqtt/test-device",
            payload='{"state":""}',
            timeout=0.01,
        )

    assert fake.subscriptions == ["zigbee2mqtt/test-device"]
    assert fake.unsubscriptions == ["zigbee2mqtt/test-device"]
    assert fake.published_topic == "zigbee2mqtt/test-device/get"
    assert fake.published_payload == '{"state":""}'


def test_wait_for_message_receives_message_during_subscribe() -> None:
    client = Zigbee2MqttClient("localhost")

    fake = FakeMqttClient()
    client._client = fake
    client._connected.set()

    original_subscribe = fake.subscribe

    def subscribe_and_respond(
        topic: str,
    ) -> tuple[int, int]:
        result = original_subscribe(topic)

        message = type(
            "Message",
            (),
            {
                "topic": topic,
                "payload": b'{"devices":["new-device"]}',
            },
        )()

        client._on_message(
            fake,
            None,
            message,
        )

        return result

    fake.subscribe = subscribe_and_respond

    payload = client.wait_for_message(
        "zigbee2mqtt/bridge/devices",
        timeout=1.0,
    )

    assert payload == b'{"devices":["new-device"]}'
    assert fake.subscriptions == ["zigbee2mqtt/bridge/devices"]
    assert fake.unsubscriptions == ["zigbee2mqtt/bridge/devices"]
