from __future__ import annotations

from pathlib import Path

from configuration_engine.profile import Profile
from configuration_engine.profile_reader import ProfileReader
from configuration_engine.profile_writer import ProfileWriter


class ProfileRepository:
    """Stores and retrieves profiles."""

    def __init__(
        self,
        directory: str | Path,
    ) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def read(
        self,
        profile_name: str,
    ) -> Profile:
        return ProfileReader.read(
            self._profile_path(profile_name),
        )

    def write(
        self,
        profile_name: str,
        profile: Profile,
    ) -> None:
        ProfileWriter.write(
            profile,
            self._profile_path(profile_name),
        )

    def exists(
        self,
        profile_name: str,
    ) -> bool:
        return self._profile_path(profile_name).exists()

    def list(
        self,
    ) -> list[str]:
        return sorted(path.stem for path in self._directory.glob("*.yaml"))

    def rename(
        self,
        old_name: str,
        new_name: str,
    ) -> None:
        """Rename a profile."""

        old_path = self._profile_path(old_name)
        new_path = self._profile_path(new_name)

        if not old_path.exists():
            raise FileNotFoundError(f'Profile "{old_name}" does not exist.')

        if new_path.exists():
            raise FileExistsError(f'Profile "{new_name}" already exists.')

        old_path.rename(new_path)

    def delete(
        self,
        profile_name: str,
    ) -> None:
        """Delete a profile."""

        path = self._profile_path(profile_name)

        if not path.exists():
            raise FileNotFoundError(f'Profile "{profile_name}" does not exist.')

        path.unlink()

    def _profile_path(
        self,
        profile_name: str,
    ) -> Path:
        return self._directory / f"{profile_name}.yaml"
