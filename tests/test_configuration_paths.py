from pathlib import Path

from configuration_engine.configuration_paths import (
    configuration_file,
    default_configuration_directory,
    ensure_configuration_directory,
    profiles_directory,
)


def test_default_configuration_directory_uses_local_app_data(
    monkeypatch,
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Test\AppData\Local")

    assert default_configuration_directory() == (
        Path(r"C:\Users\Test\AppData\Local") / "configuration_engine"
    )


def test_default_configuration_directory_falls_back_to_home(
    monkeypatch,
) -> None:
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    assert default_configuration_directory() == (Path.home() / "configuration_engine")


def test_configuration_file_uses_supplied_directory() -> None:
    directory = Path("test-config")

    assert configuration_file(directory) == directory / "config.yaml"


def test_profiles_directory_uses_supplied_directory() -> None:
    directory = Path("test-config")

    assert profiles_directory(directory) == directory / "profiles"


def test_ensure_configuration_directory_creates_directory(
    tmp_path,
) -> None:
    directory = tmp_path / "configuration_engine"

    result = ensure_configuration_directory(directory)

    assert result == directory
    assert directory.is_dir()
