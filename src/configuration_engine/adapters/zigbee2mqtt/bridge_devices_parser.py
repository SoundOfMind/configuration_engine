from __future__ import annotations

import json

from configuration_engine.device_summary import DeviceSummary


class BridgeDevicesParser:
    """Parse the Zigbee2MQTT bridge device list."""

    def parse(
        self,
        payload: str,
    ) -> list[DeviceSummary]:
        """Parse the bridge device list."""

        device_objects = json.loads(payload)

        devices: list[DeviceSummary] = []

        for obj in device_objects:
            if obj.get("type") == "Coordinator":
                continue

            devices.append(
                DeviceSummary(
                    friendly_name=obj["friendly_name"],
                    ieee_address=obj["ieee_address"],
                    manufacturer=obj["manufacturer"],
                    model_id=obj["model_id"],
                    firmware=obj.get("software_build_id"),
                )
            )

        return sorted(
            devices,
            key=lambda device: device.friendly_name.lower(),
        )
