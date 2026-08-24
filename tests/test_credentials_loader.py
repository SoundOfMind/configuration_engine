from pathlib import Path

import pytest
import yaml

from configuration_engine.configuration_paths import credentials_file
from configuration_engine.credentials import MqttCredentials
from configuration_engine.credentials_loader import CredentialsLoader


def test_create_and_load_credentials(
    tmp_path: Path,
) -> None:
    path = tmp_path / "credentials.yaml"

    credentials = MqttCredentials(
        username="test-user",
        password="test-password",
    )

    CredentialsLoader.create(
        path,
        credentials,
    )

    assert CredentialsLoader.load(path) == credentials

    document = yaml.safe_load(
        path.read_text(encoding="utf-8"),
    )

    assert document == {
        "mqtt": {
            "username": "test-user",
            "password": "test-password",
        },
    }


def test_create_refuses_to_overwrite(
    tmp_path: Path,
) -> None:
    path = tmp_path / "credentials.yaml"
    path.write_text("mqtt: {}\n", encoding="utf-8")

    credentials = MqttCredentials(
        username="test-user",
        password="test-password",
    )

    with pytest.raises(FileExistsError):
        CredentialsLoader.create(
            path,
            credentials,
        )


def test_save_updates_existing_credentials(
    tmp_path: Path,
) -> None:
    path = tmp_path / "credentials.yaml"

    original = MqttCredentials(
        username="old-user",
        password="old-password",
    )

    updated = MqttCredentials(
        username="new-user",
        password="new-password",
    )

    CredentialsLoader.create(
        path,
        original,
    )

    CredentialsLoader.save(
        path,
        updated,
    )

    assert CredentialsLoader.load(path) == updated


def test_save_preserves_read_only_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "credentials.yaml"

    credentials = MqttCredentials(
        username="test-user",
        password="test-password",
    )

    CredentialsLoader.create(
        path,
        credentials,
    )

    original_mode = path.stat().st_mode

    CredentialsLoader.save(
        path,
        credentials,
    )

    assert path.stat().st_mode == original_mode


def test_load_empty_credentials_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "credentials.yaml"
    path.write_text("{}\n", encoding="utf-8")

    assert CredentialsLoader.load(path) == MqttCredentials()


def test_credentials_file_uses_supplied_directory() -> None:
    directory = Path("test-config")

    assert credentials_file(directory) == directory / "credentials.yaml"


def test_save_failure_preserves_original_credentials(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "credentials.yaml"

    original = MqttCredentials(
        username="old-user",
        password="old-password",
    )

    updated = MqttCredentials(
        username="new-user",
        password="new-password",
    )

    CredentialsLoader.create(
        path,
        original,
    )

    original_contents = path.read_text(
        encoding="utf-8",
    )

    replace_calls = 0

    def fail_replace(
        source: Path,
        destination: Path,
    ) -> None:
        nonlocal replace_calls

        del source, destination

        replace_calls += 1

        raise PermissionError("simulated replacement failure")

    monkeypatch.setattr(
        "configuration_engine.credentials_loader.os.replace",
        fail_replace,
    )

    with pytest.raises(PermissionError):
        CredentialsLoader.save(
            path,
            updated,
        )

    assert replace_calls == 2

    assert (
        path.read_text(
            encoding="utf-8",
        )
        == original_contents
    )

    assert CredentialsLoader.load(path) == original

    assert path.stat().st_mode & 0o222 == 0

    temporary_files = list(
        tmp_path.glob(".credentials.yaml.*.tmp"),
    )

    assert temporary_files == []
