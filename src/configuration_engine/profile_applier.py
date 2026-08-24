from __future__ import annotations

import time
from collections.abc import Callable

from configuration_engine.backend import Backend
from configuration_engine.profile import Profile
from configuration_engine.profile_difference import (
    ProfileDifference,
    PropertyDifference,
)

WRITE_DELAY = 1.0


class ProfileApplier:
    """Applies and verifies profile changes through a backend."""

    def __init__(self, backend: Backend) -> None:
        self._backend = backend

    def apply(
        self,
        device: str,
        current: Profile,
        desired: Profile,
        timeout: float,
        on_progress: Callable[[str], None] | None = None,
    ) -> ProfileDifference:
        """Apply profile differences and verify the resulting device state."""

        profile_difference = self._compare_for_application(
            current,
            desired,
        )

        if profile_difference.is_empty:
            return profile_difference

        total = len(profile_difference.differences)

        for index, item in enumerate(
            profile_difference.differences,
            start=1,
        ):
            if on_progress is not None:
                on_progress(
                    f"Applying change {index} of {total}...",
                )

            self._backend.set_property(
                device,
                item.property_name,
                item.desired_value,
                timeout,
            )

        if on_progress is not None:
            on_progress("Verifying changes...")

        deadline = time.monotonic() + timeout

        while True:
            snapshot = self._backend.snapshot(
                device,
                timeout,
            )

            current = Profile.from_snapshot(snapshot)

            remaining = self._compare_for_application(
                current,
                desired,
            )

            if remaining.is_empty:
                return profile_difference

            if time.monotonic() >= deadline:
                return remaining

            time.sleep(WRITE_DELAY)

    def _compare_for_application(
        self,
        current: Profile,
        desired: Profile,
    ) -> ProfileDifference:
        """Compare only properties that are applicable to the desired profile."""

        differences: list[PropertyDifference] = []

        for property_name, desired_value in desired.values.items():
            current_value = current.values.get(property_name)

            if current_value != desired_value:
                differences.append(
                    PropertyDifference(
                        property_name=property_name,
                        current_value=current_value,
                        desired_value=desired_value,
                    )
                )

        return ProfileDifference(differences)
