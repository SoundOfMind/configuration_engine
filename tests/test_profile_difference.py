from __future__ import annotations

from configuration_engine.profile_difference import (
    ProfileDifference,
    PropertyDifference,
)


def test_empty_difference() -> None:
    difference = ProfileDifference([])

    assert difference.is_empty


def test_non_empty_difference() -> None:
    difference = ProfileDifference(
        [
            PropertyDifference(
                property_name="minimumLevel",
                current_value=20,
                desired_value=40,
            ),
        ],
    )

    assert not difference.is_empty
