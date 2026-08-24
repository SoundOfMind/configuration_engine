from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any

import yaml

from configuration_engine.credentials import MqttCredentials


class CredentialsLoader:
    """Loads and persists private MQTT credentials."""

    @staticmethod
    def load(
        path: str | Path,
    ) -> MqttCredentials:
        """Load MQTT credentials."""

        credentials_path = Path(path)

        with credentials_path.open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)

        if document is None:
            document = {}

        if not isinstance(document, dict):
            raise TypeError("Credentials document must be a YAML mapping.")

        mqtt = document.get("mqtt", {})

        if not isinstance(mqtt, dict):
            raise TypeError("'mqtt' must be a mapping.")

        return MqttCredentials(
            username=mqtt.get("username"),
            password=mqtt.get("password"),
        )

    @staticmethod
    def create(
        path: str | Path,
        credentials: MqttCredentials,
    ) -> None:
        """Create a new credentials file."""

        credentials_path = Path(path)

        if credentials_path.exists():
            raise FileExistsError(credentials_path)

        credentials_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        document: dict[str, Any] = {
            "mqtt": {
                "username": credentials.username,
                "password": credentials.password,
            },
        }

        with credentials_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as stream:
            yaml.safe_dump(
                document,
                stream,
                sort_keys=False,
            )

        CredentialsLoader._make_read_only(credentials_path)

    @staticmethod
    def save(
        path: str | Path,
        credentials: MqttCredentials,
    ) -> None:
        """Persist MQTT credentials with an atomic write."""

        credentials_path = Path(path)

        if not credentials_path.is_file():
            raise FileNotFoundError(credentials_path)

        document: dict[str, Any] = {
            "mqtt": {
                "username": credentials.username,
                "password": credentials.password,
            },
        }

        original_mode = stat.S_IMODE(
            credentials_path.stat().st_mode,
        )

        temporary_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{credentials_path.name}.",
            suffix=".tmp",
            dir=credentials_path.parent,
        )

        os.close(temporary_descriptor)

        temporary_path = Path(temporary_name)

        try:
            with temporary_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as file:
                yaml.safe_dump(
                    document,
                    file,
                    sort_keys=False,
                )
                file.flush()
                os.fsync(file.fileno())

            temporary_path.chmod(
                original_mode & ~0o222,
            )

            try:
                os.replace(
                    temporary_path,
                    credentials_path,
                )
            except PermissionError:
                credentials_path.chmod(
                    original_mode | stat.S_IWUSR,
                )
                os.replace(
                    temporary_path,
                    credentials_path,
                )

            CredentialsLoader._make_read_only(
                credentials_path,
            )

        finally:
            if temporary_path.exists():
                temporary_path.chmod(
                    original_mode | stat.S_IWUSR,
                )
                temporary_path.unlink()

            if credentials_path.exists():
                credentials_path.chmod(
                    original_mode & ~0o222,
                )

    @staticmethod
    def _make_read_only(path: Path) -> None:
        current_mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(current_mode & ~0o222)

        mode = stat.S_IMODE(path.stat().st_mode)

        if mode & 0o222:
            raise PermissionError(f"Credentials file must be read-only: {path}")
