from __future__ import annotations

import multiprocessing
import stat
import time
from pathlib import Path
from typing import Any

import pytest
import yaml

from configuration_engine.backend_configuration import BackendConfiguration
from configuration_engine.configuration import Configuration
from configuration_engine.configuration_loader import ConfigurationLoader, _FileLock
from configuration_engine.mqtt_configuration import MqttConfiguration


def _configuration() -> Configuration:
    return Configuration(
        backend=BackendConfiguration(name="zigbee2mqtt"),
        mqtt=MqttConfiguration(host="192.168.1.24"),
    )


def _write_configuration(path: Path, document: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    path.chmod(stat.S_IMODE(path.stat().st_mode) & ~0o222)


def _hold_lock(
    path: str,
    ready: multiprocessing.synchronize.Event,
    release: multiprocessing.synchronize.Event,
) -> None:
    with _FileLock(Path(path)):
        ready.set()
        release.wait()


def test_file_lock_blocks_another_process(tmp_path: Path) -> None:
    lock_path = tmp_path / "config.yaml.lock"

    context = multiprocessing.get_context("spawn")
    holder_ready = context.Event()
    holder_release = context.Event()

    holder = context.Process(
        target=_hold_lock,
        args=(str(lock_path), holder_ready, holder_release),
    )
    holder.start()

    try:
        assert holder_ready.wait(timeout=5)

        contender_ready = context.Event()
        contender_release = context.Event()

        contender = context.Process(
            target=_hold_lock,
            args=(str(lock_path), contender_ready, contender_release),
        )
        contender.start()

        try:
            time.sleep(0.5)

            assert not contender_ready.is_set()

            holder_release.set()

            assert contender_ready.wait(timeout=5)
            contender_release.set()
            contender.join(timeout=5)
            assert contender.exitcode == 0
        finally:
            if contender.is_alive():
                contender.terminate()
                contender.join()
    finally:
        holder_release.set()
        if holder.is_alive():
            holder.terminate()
            holder.join()


def _document() -> dict[str, Any]:
    return {
        "backend": {"name": "zigbee2mqtt"},
        "mqtt": {"host": "192.168.1.24", "port": 1883},
        "defaults": {"timeout": 45.0},
        "mqtt_get_properties": {},
    }


def _is_read_only(path: Path) -> bool:
    return stat.S_IMODE(path.stat().st_mode) & 0o222 == 0


def test_save_requires_read_only_configuration(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(_document()), encoding="utf-8")

    with pytest.raises(PermissionError, match="read-only"):
        ConfigurationLoader.save(path, _configuration())


def test_save_creates_backup_and_restores_read_only(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    original = _document()
    _write_configuration(path, original)

    ConfigurationLoader.save(path, _configuration())

    backup = path.with_name("config.yaml.bak")
    assert backup.is_file()
    assert yaml.safe_load(backup.read_text(encoding="utf-8")) == original
    assert ConfigurationLoader.load(path) == _configuration()
    assert _is_read_only(path)
    assert _is_read_only(backup)


def test_update_mqtt_get_property_persists_discovery(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_configuration(path, _document())

    changed = ConfigurationLoader.update_mqtt_get_property(
        path,
        "Inovelli",
        "VZM31-SN",
        "levelConfigOnLevel",
    )

    assert changed is True
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert document["mqtt_get_properties"] == {"Inovelli": {"VZM31-SN": "levelConfigOnLevel"}}
    assert _is_read_only(path)


def test_update_mqtt_get_property_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_configuration(path, _document())

    assert (
        ConfigurationLoader.update_mqtt_get_property(
            path, "Inovelli", "VZM31-SN", "levelConfigOnLevel"
        )
        is True
    )
    backup = path.with_name("config.yaml.bak")
    backup_mtime = backup.stat().st_mtime_ns

    assert (
        ConfigurationLoader.update_mqtt_get_property(
            path, "Inovelli", "VZM31-SN", "levelConfigOnLevel"
        )
        is False
    )
    assert backup.stat().st_mtime_ns == backup_mtime


def test_update_mqtt_get_property_preserves_existing_properties(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    document = _document()
    document["mqtt_get_properties"] = {"Inovelli": {"VZM30-SN": "someProperty"}}
    _write_configuration(path, document)

    assert (
        ConfigurationLoader.update_mqtt_get_property(
            path, "Inovelli", "VZM31-SN", "levelConfigOnLevel"
        )
        is True
    )

    restored = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert restored["mqtt_get_properties"] == {
        "Inovelli": {
            "VZM30-SN": "someProperty",
            "VZM31-SN": "levelConfigOnLevel",
        }
    }


def test_update_mqtt_get_property_rejects_writable_configuration(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(_document()), encoding="utf-8")

    with pytest.raises(PermissionError, match="read-only"):
        ConfigurationLoader.update_mqtt_get_property(
            path, "Inovelli", "VZM31-SN", "levelConfigOnLevel"
        )


def test_save_validates_serialized_temporary_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "config.yaml"
    original = _document()
    _write_configuration(path, original)

    def write_invalid_yaml(
        document: object,
        stream: Any,
        *,
        sort_keys: bool,
    ) -> None:
        del document, sort_keys
        stream.write("backend: [invalid\n")

    monkeypatch.setattr(yaml, "safe_dump", write_invalid_yaml)

    with pytest.raises(yaml.YAMLError):
        ConfigurationLoader.save(path, _configuration())

    assert yaml.safe_load(path.read_text(encoding="utf-8")) == original
    assert _is_read_only(path)


def test_save_rejects_invalid_current_configuration(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_configuration(path, {"backend": {"name": "zigbee2mqtt"}})

    with pytest.raises(ValueError, match="mqtt.host"):
        ConfigurationLoader.save(path, _configuration())


def test_update_rejects_invalid_current_configuration(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_configuration(path, {"backend": {"name": "zigbee2mqtt"}})

    with pytest.raises(ValueError, match="mqtt.host"):
        ConfigurationLoader.update_mqtt_get_property(
            path, "Inovelli", "VZM31-SN", "levelConfigOnLevel"
        )
