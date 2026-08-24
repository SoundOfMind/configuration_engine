from pathlib import Path

import pytest

from configuration_engine.settings import SettingsScreen


def test_remove_old_configuration_directory_removes_empty_directory(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "old-configuration"
    directory.mkdir()

    settings = SettingsScreen.__new__(SettingsScreen)

    settings._remove_old_configuration_directory(directory)

    assert not directory.exists()


def test_remove_old_configuration_directory_refuses_non_empty_directory(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "old-configuration"
    directory.mkdir()

    (directory / "credentials.yaml").write_text(
        "important data\n",
        encoding="utf-8",
    )

    settings = SettingsScreen.__new__(SettingsScreen)

    with pytest.raises(
        OSError,
        match="Old configuration directory is not empty",
    ):
        settings._remove_old_configuration_directory(directory)

    assert directory.exists()
    assert (directory / "credentials.yaml").exists()
