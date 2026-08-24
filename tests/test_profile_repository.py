from __future__ import annotations

from pathlib import Path

import pytest

from configuration_engine.profile import Profile
from configuration_engine.profile_repository import ProfileRepository


def _profile() -> Profile:
    return Profile(
        vendor="Test",
        model="TestModel",
        values={},
    )


def test_rename_profile(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path)
    repository.write("Old Profile", _profile())

    repository.rename(
        "Old Profile",
        "New Profile",
    )

    assert repository.exists("Old Profile") is False
    assert repository.exists("New Profile") is True


def test_rename_missing_profile_raises(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match=r'Profile "Missing" does not exist\.',
    ):
        repository.rename(
            "Missing",
            "New Profile",
        )


def test_rename_existing_profile_raises(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path)
    repository.write("Old Profile", _profile())
    repository.write("Existing Profile", _profile())

    with pytest.raises(
        FileExistsError,
        match=r'Profile "Existing Profile" already exists\.',
    ):
        repository.rename(
            "Old Profile",
            "Existing Profile",
        )


def test_delete_profile(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path)
    repository.write("Test Profile", _profile())

    repository.delete("Test Profile")

    assert repository.exists("Test Profile") is False


def test_delete_missing_profile_raises(tmp_path: Path) -> None:
    repository = ProfileRepository(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match=r'Profile "Missing" does not exist\.',
    ):
        repository.delete("Missing")
