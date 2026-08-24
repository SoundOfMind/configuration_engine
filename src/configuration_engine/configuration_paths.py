from __future__ import annotations

import os
from pathlib import Path

import yaml

APPLICATION_DIRECTORY_NAME = "configuration_engine"
CONFIGURATION_FILE_NAME = "config.yaml"
CREDENTIALS_FILE_NAME = "credentials.yaml"
PROFILES_DIRECTORY_NAME = "profiles"
LOCATION_FILE_NAME = "location.yaml"


def default_configuration_directory() -> Path:
    """Return the default user configuration directory.

    On Windows this uses LOCALAPPDATA when available. Otherwise it
    falls back to the user's home directory.
    """

    value = os.environ.get("LOCALAPPDATA")

    if value:
        return Path(value) / APPLICATION_DIRECTORY_NAME

    return Path.home() / APPLICATION_DIRECTORY_NAME


def location_file() -> Path:
    """Return the path to the configuration-location pointer file."""

    return default_configuration_directory() / LOCATION_FILE_NAME


def active_configuration_directory() -> Path:
    """Return the directory containing the active configuration."""

    pointer = default_configuration_directory() / LOCATION_FILE_NAME

    if not pointer.exists():
        return default_configuration_directory()

    with pointer.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise TypeError("Invalid configuration location file.")

    value = data.get("configuration_directory")

    if not isinstance(value, str) or not value:
        raise ValueError("Invalid configuration directory.")

    return Path(value)


def configuration_file(
    configuration_directory: Path | None = None,
) -> Path:
    """Return the path to the application's configuration file."""

    if configuration_directory is None:
        directory = active_configuration_directory()
    else:
        directory = configuration_directory

    return directory / CONFIGURATION_FILE_NAME


def credentials_file(
    configuration_directory: Path | None = None,
) -> Path:
    """Return the path to the application's credentials file."""

    if configuration_directory is None:
        directory = active_configuration_directory()
    else:
        directory = configuration_directory

    return directory / CREDENTIALS_FILE_NAME


def profiles_directory(
    configuration_directory: Path | None = None,
) -> Path:
    """Return the path to the application's profile directory."""

    if configuration_directory is None:
        directory = active_configuration_directory()
    else:
        directory = configuration_directory

    return directory / PROFILES_DIRECTORY_NAME


def ensure_configuration_directory(
    configuration_directory: Path | None = None,
) -> Path:
    """Create and return the application's configuration directory."""

    if configuration_directory is None:
        directory = active_configuration_directory()
    else:
        directory = configuration_directory

    directory.mkdir(parents=True, exist_ok=True)

    return directory
