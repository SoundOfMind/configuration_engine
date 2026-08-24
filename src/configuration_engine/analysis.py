from __future__ import annotations

from dataclasses import dataclass

from configuration_engine.recommendation import Recommendation


@dataclass(frozen=True, slots=True)
class Analysis:
    """Analysis of a device."""

    device: str

    model: str | None

    recommendations: list[Recommendation]
