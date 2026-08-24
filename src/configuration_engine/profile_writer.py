from __future__ import annotations

from pathlib import Path

import yaml

from configuration_engine.profile import Profile


class ProfileWriter:
    """Writes profiles to YAML files."""

    @staticmethod
    def write(
        profile: Profile,
        path: str | Path,
    ) -> None:
        document = {
            "vendor": profile.vendor,
            "model": profile.model,
            "values": profile.values,
        }

        with Path(path).open(
            "w",
            encoding="utf-8",
        ) as stream:
            yaml.safe_dump(
                document,
                stream,
                allow_unicode=True,
                sort_keys=False,
            )
