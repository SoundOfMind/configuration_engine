from __future__ import annotations

from pathlib import Path

from configuration_engine.profile import Profile
from configuration_engine.profile_reader import ProfileReader
from configuration_engine.profile_writer import ProfileWriter


def test_profile_round_trip(
    tmp_path: Path,
) -> None:
    profile = Profile(
        vendor="Inovelli",
        model="VZM31-SN",
        values={
            "minimumLevel": 40,
            "maximumLevel": 255,
        },
    )

    path = tmp_path / "bedtime.yaml"

    ProfileWriter.write(profile, path)

    restored = ProfileReader.read(path)

    assert restored == profile
