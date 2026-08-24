from __future__ import annotations

import json
from typing import Any

from configuration_engine.device_snapshot import DeviceSnapshot


class SnapshotParser:
    """Parses Zigbee2MQTT MQTT payloads into DeviceSnapshot objects."""

    def parse(
        self,
        *,
        device_id: str,
        payload: str,
    ) -> DeviceSnapshot:
        values: dict[str, Any] = json.loads(payload)

        return DeviceSnapshot(
            backend="zigbee2mqtt",
            device_id=device_id,
            model=None,
            values=values,
        )
