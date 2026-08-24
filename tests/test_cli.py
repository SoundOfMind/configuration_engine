from __future__ import annotations

from typing import NoReturn

import pytest
from typer.testing import CliRunner

from configuration_engine import cli
from configuration_engine.configuration_engine import ConfigurationEngine
from configuration_engine.profile import Profile
from configuration_engine.profile_difference import (
    ProfileDifference,
    PropertyDifference,
)

runner = CliRunner()


def test_snapshot_reports_missing_device_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeEngine:
        def snapshot(self, device_id: str) -> NoReturn:
            raise ValueError(f'Device "{device_id}" was not found in the Zigbee2MQTT device list.')

    monkeypatch.setattr(
        ConfigurationEngine,
        "from_file",
        lambda config: FakeEngine(),
    )

    result = runner.invoke(
        cli.app,
        ["snapshot", "Definitely Not A Device"],
    )

    assert result.exit_code == 1
    assert (
        'Error: Device "Definitely Not A Device" was not found in the Zigbee2MQTT device list.'
        in result.output
    )
    assert "Traceback" not in result.output


def test_compare_aligns_difference_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeEngine:
        def compare(self, device: str, profile: Profile) -> ProfileDifference:
            return ProfileDifference(
                [
                    PropertyDifference(
                        property_name="brightnessLevelForDoubleTapDown",
                        current_value=60,
                        desired_value=20,
                    ),
                    PropertyDifference(
                        property_name="ledColorWhenOn",
                        current_value=212,
                        desired_value=85,
                    ),
                    PropertyDifference(
                        property_name="ledIntensityWhenOn",
                        current_value=74,
                        desired_value=98,
                    ),
                ]
            )

    monkeypatch.setattr(
        ConfigurationEngine,
        "from_file",
        lambda config: FakeEngine(),
    )

    monkeypatch.setattr(
        cli,
        "ProfileReader",
        type(
            "FakeProfileReader",
            (),
            {
                "read": staticmethod(
                    lambda path: Profile(
                        vendor=None,
                        model=None,
                        values={},
                    )
                )
            },
        ),
    )

    result = runner.invoke(
        cli.app,
        ["compare", "Test2", "Test1-clone-source2"],
    )

    assert result.exit_code == 0
    assert "Property" in result.output
    assert "Test2" in result.output
    assert "Test1-clone-source2" in result.output
    assert "brightnessLevelForDoubleTapDown" in result.output
