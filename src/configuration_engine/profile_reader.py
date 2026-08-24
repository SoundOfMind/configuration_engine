from __future__ import annotations

from pathlib import Path

import yaml

from configuration_engine.profile import Profile


class ProfileReader:
    """Reads profiles from YAML files."""

    @staticmethod
    def read(
        path: str | Path,
    ) -> Profile:
        with Path(path).open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)

        return Profile(
            vendor=document.get("vendor"),
            model=document.get("model"),
            values=document["values"],
        )
