from __future__ import annotations

from configuration_engine.device_snapshot import DeviceSnapshot


class SnapshotFormatter:
    """Formats device snapshots for display."""

    @staticmethod
    def format(snapshot: DeviceSnapshot) -> str:
        lines: list[str] = []

        lines.append(f"Backend : {snapshot.backend}")
        lines.append(f"Device  : {snapshot.device_id}")

        if snapshot.model is not None:
            lines.append(f"Model   : {snapshot.model}")

        lines.append("")
        lines.append("Properties")
        lines.append("----------")

        for name in sorted(snapshot.values):
            value = snapshot.values[name]
            lines.append(f"{name:<35} {value}")

        return "\n".join(lines)
