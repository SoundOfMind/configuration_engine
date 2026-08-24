from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DeviceSnapshot:
    """
    Raw device state as reported by a backend.

    Property names remain backend-native.
    """

    backend: str
    device_id: str
    model: str | None
    values: Mapping[str, Any]
