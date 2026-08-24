import pytest

from configuration_engine.setup_helpers import validate_mqtt_settings


def test_validate_mqtt_settings_returns_typed_settings() -> None:
    settings = validate_mqtt_settings(
        "localhost",
        "1883",
        "user",
        "password",
    )

    assert settings.host == "localhost"
    assert settings.port == 1883
    assert settings.username == "user"
    assert settings.password == "password"


@pytest.mark.parametrize(
    ("host", "port", "username", "password", "message"),
    [
        ("", "1883", "user", "password", "MQTT host is required."),
        ("localhost", "abc", "user", "password", "MQTT port must be a number."),
        ("localhost", "0", "user", "password", "MQTT port must be between 1 and 65535."),
        ("localhost", "65536", "user", "password", "MQTT port must be between 1 and 65535."),
        ("localhost", "1883", "", "password", "MQTT username is required."),
        ("localhost", "1883", "user", "", "MQTT password is required."),
    ],
)
def test_validate_mqtt_settings_rejects_invalid_values(
    host: str,
    port: str,
    username: str,
    password: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_mqtt_settings(host, port, username, password)


def test_write_location_pointer_for_non_default_directory(
    tmp_path,
    monkeypatch,
) -> None:
    from configuration_engine import setup_helpers

    pointer = tmp_path / "location.yaml"
    default_directory = tmp_path / "default"
    selected_directory = tmp_path / "selected"

    monkeypatch.setattr(setup_helpers, "location_file", lambda: pointer)
    monkeypatch.setattr(
        setup_helpers,
        "default_configuration_directory",
        lambda: default_directory,
    )

    setup_helpers.write_location_pointer(selected_directory)

    assert pointer.exists()
    assert pointer.read_text(encoding="utf-8") == (
        "configuration_directory: " + str(selected_directory) + "\n"
    )
    assert not pointer.with_suffix(".yaml.tmp").exists()


def test_write_location_pointer_removes_pointer_for_default_directory(
    tmp_path,
    monkeypatch,
) -> None:
    from configuration_engine import setup_helpers

    pointer = tmp_path / "location.yaml"
    default_directory = tmp_path / "default"

    pointer.write_text(
        "configuration_directory: old\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(setup_helpers, "location_file", lambda: pointer)
    monkeypatch.setattr(
        setup_helpers,
        "default_configuration_directory",
        lambda: default_directory,
    )

    setup_helpers.write_location_pointer(default_directory)

    assert not pointer.exists()
