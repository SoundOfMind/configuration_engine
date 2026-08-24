from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from configuration_engine.device_snapshot import DeviceSnapshot
from configuration_engine.profile_difference import (
    ProfileDifference,
    PropertyDifference,
)


@dataclass(frozen=True, slots=True)
class Profile:
    """Desired configuration for a device."""

    vendor: str | None
    model: str | None
    values: dict[str, Any]

    @classmethod
    def from_snapshot(
        cls,
        snapshot: DeviceSnapshot,
        vendor: str | None = None,
        model: str | None = None,
    ) -> Profile:
        """Create a profile from a device snapshot."""

        values = dict(snapshot.values)

        return cls(
            vendor=vendor,
            model=snapshot.model if model is None else model,
            values=values,
        )

    def compare(
        self,
        desired: Profile,
    ) -> ProfileDifference:
        """Compare this profile to the desired profile."""

        differences: list[PropertyDifference] = []

        for property_name in sorted(desired.values):
            current_value = self.values.get(property_name)
            desired_value = desired.values[property_name]

            if current_value != desired_value:
                differences.append(
                    PropertyDifference(
                        property_name=property_name,
                        current_value=current_value,
                        desired_value=desired_value,
                    )
                )

        return ProfileDifference(differences)
