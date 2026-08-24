from __future__ import annotations

from pathlib import Path

import typer

from configuration_engine.configuration_engine import ConfigurationEngine
from configuration_engine.configuration_paths import (
    configuration_file,
    profiles_directory,
)
from configuration_engine.device_definition import DeviceProperty
from configuration_engine.device_summary import DeviceSummary
from configuration_engine.profile_reader import ProfileReader
from configuration_engine.profile_repository import ProfileRepository

from . import __version__

app = typer.Typer(help="Deterministic configuration management for home automation devices")


@app.command()
def version() -> None:
    """Display the application version."""
    typer.echo(__version__)


@app.command()
def snapshot(
    device_id: list[str],
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Display property values one per line.",
    ),
    config: Path | None = None,
) -> None:
    """Display the current state of a device."""

    if config is None:
        config = configuration_file()

    device = " ".join(device_id)

    engine = ConfigurationEngine.from_file(config)

    try:
        snapshot = engine.snapshot(device)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not verbose:
        from .snapshot_formatter import SnapshotFormatter

        typer.echo(SnapshotFormatter.format(snapshot))
        return

    typer.echo()
    typer.echo(device)
    typer.echo("=" * len(device))
    typer.echo()
    typer.echo(f"Backend : {snapshot.backend}")

    if snapshot.model is not None:
        typer.echo(f"Model   : {snapshot.model}")

    typer.echo()

    for property_name in sorted(snapshot.values):
        value = snapshot.values[property_name]
        typer.echo(f"{property_name:<28} {value}")


@app.command()
def devices(
    config: Path | None = None,
) -> None:
    """List available devices."""

    if config is None:
        config = configuration_file()

    engine = ConfigurationEngine.from_file(config)

    devices = engine.devices()

    if not devices:
        typer.echo("No devices found.")
        return

    _print_devices(devices)


@app.command()
def info(
    device: list[str],
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Display detailed property metadata.",
    ),
    config: Path | None = None,
) -> None:
    """Display information about a device."""

    if config is None:
        config = configuration_file()

    engine = ConfigurationEngine.from_file(config)

    device_name = " ".join(device)

    definition = engine.definition(device_name)

    typer.echo()
    typer.echo(device_name)
    typer.echo("=" * len(device_name))
    typer.echo()

    typer.echo(f"Description : {definition.description}")
    typer.echo(f"Model       : {definition.model}")
    typer.echo(f"Vendor      : {definition.vendor}")
    typer.echo(f"Version     : {definition.version}")
    typer.echo()

    typer.echo("Properties")
    typer.echo("----------")

    for property in definition.properties:
        _print_property(
            property,
            verbose,
        )


@app.command()
def capture(
    profile_name: str,
    device: str,
    config: Path | None = None,
) -> None:
    """Capture a device configuration as a profile."""

    if config is None:
        config = configuration_file()

    engine = ConfigurationEngine.from_file(config)

    profile = engine.capture(device)

    repository = ProfileRepository(
        profiles_directory(config.parent),
    )

    repository.write(
        profile_name,
        profile,
    )

    typer.echo(f'Profile "{profile_name}" captured.')


@app.command()
def compare(
    device: str,
    profile_name: str,
    config: Path | None = None,
) -> None:
    """Compare a device with a profile."""

    if config is None:
        config = configuration_file()

    engine = ConfigurationEngine.from_file(config)

    profile = ProfileReader.read(
        profiles_directory(config.parent) / f"{profile_name}.yaml",
    )

    difference = engine.compare(
        device,
        profile,
    )

    if difference.is_empty:
        typer.echo("Profiles match.")
        return

    typer.echo(f"{len(difference.differences)} difference(s):")

    property_width = max(len(item.property_name) for item in difference.differences)

    current_width = max(len(str(item.current_value)) for item in difference.differences)

    desired_width = max(len(str(item.desired_value)) for item in difference.differences)

    table_width = property_width + 2 + current_width + 2 + desired_width

    typer.echo(
        f"{'Property':<{property_width}}  "
        f"{device:<{current_width}}  "
        f"{profile_name:<{desired_width}}"
    )

    typer.echo("-" * table_width)

    for item in difference.differences:
        typer.echo(
            f"{item.property_name:<{property_width}}  "
            f"{item.current_value!s:>{current_width}}  "
            f"{item.desired_value!s:>{desired_width}}"
        )


@app.command()
def apply(
    device: str,
    profile_name: str,
    config: Path | None = None,
) -> None:
    """Apply a profile to a device."""

    if config is None:
        config = configuration_file()

    typer.echo(f'Applying profile "{profile_name}" to {device}...')
    typer.echo("This may take a few seconds...")
    typer.echo()

    engine = ConfigurationEngine.from_file(config)

    repository = ProfileRepository(
        profiles_directory(config.parent),
    )

    profile = repository.read(profile_name)

    profile_difference = engine.apply(
        device,
        profile,
    )

    if profile_difference.is_empty:
        typer.echo("Profile already matches.")
        typer.echo("No changes required.")
        return

    typer.echo(f"{len(profile_difference.differences)} change(s) applied.")
    typer.echo()

    for item in profile_difference.differences:
        typer.echo(f"✓ {item.property_name}: {item.current_value} → {item.desired_value}")

    typer.echo()
    typer.echo("Profile applied successfully.")


@app.command()
def profiles(
    config: Path | None = None,
) -> None:
    """List available profiles."""

    if config is None:
        config = configuration_file()

    repository = ProfileRepository(
        profiles_directory(config.parent),
    )

    names = repository.list()

    if not names:
        typer.echo("No profiles found.")
        return

    typer.echo("Profiles:")

    for name in names:
        typer.echo(f"  {name}")


@app.command()
def rename(
    old_name: str,
    new_name: str,
    config: Path | None = None,
) -> None:
    """Rename a profile."""

    if config is None:
        config = configuration_file()

    repository = ProfileRepository(
        profiles_directory(config.parent),
    )

    repository.rename(
        old_name,
        new_name,
    )

    typer.echo(f'Profile "{old_name}" renamed to "{new_name}".')


@app.command()
def delete(
    profile_name: str,
    config: Path | None = None,
) -> None:
    """Delete a profile."""

    if config is None:
        config = configuration_file()

    repository = ProfileRepository(
        profiles_directory(config.parent),
    )

    repository.delete(profile_name)

    typer.echo(f'Profile "{profile_name}" deleted.')


def _print_devices(
    devices: list[DeviceSummary],
) -> None:
    """Display the available devices."""

    typer.echo()

    typer.echo(f"{'Name':<28} {'Vendor':<10} {'Model':<12} {'FW':<6} IEEE Address")

    typer.echo(f"{'-' * 28} {'-' * 10} {'-' * 12} {'-' * 6} {'-' * 16}")

    for device in devices:
        name = "<unnamed>" if device.friendly_name == device.ieee_address else device.friendly_name

        typer.echo(
            f"{name:<28} "
            f"{device.manufacturer:<10} "
            f"{device.model_id:<12} "
            f"{(device.firmware or '-'):6} "
            f"{device.ieee_address}"
        )


def _print_property(
    property: DeviceProperty,
    verbose: bool,
) -> None:
    """Display a device property."""

    typer.echo(property.name)

    if not verbose:
        return

    typer.echo(f"    Type        : {property.property_type}")

    if property.access is not None:
        typer.echo(f"    Access      : {property.access}")

    if property.category is not None:
        typer.echo(f"    Category    : {property.category}")

    if property.unit is not None:
        typer.echo(f"    Unit        : {property.unit}")

    if property.description is not None:
        typer.echo(f"    Description : {property.description}")

    if property.values:
        typer.echo("    Values:")

        for value in property.values:
            typer.echo(f"        {value}")

    typer.echo()


@app.command()
def analyze(
    device_id: list[str],
    config: Path | None = None,
) -> None:
    """Analyze a device and display property recommendations."""

    if config is None:
        config = configuration_file()

    device = " ".join(device_id)

    engine = ConfigurationEngine.from_file(config)
    analysis = engine.analyze(device)

    typer.echo()
    typer.echo(analysis.device)
    typer.echo("=" * len(analysis.device))

    if analysis.model:
        typer.echo(f"Model: {analysis.model}")

    typer.echo()
    typer.echo("Recommendations")
    typer.echo("---------------")

    for recommendation in analysis.recommendations:
        action = "include" if recommendation.include else "exclude"

        typer.echo()
        typer.echo(recommendation.property.name)
        typer.echo(f"    Action     : {action}")
        typer.echo(f"    Confidence : {int(recommendation.confidence)}%")
        typer.echo(f"    Reason     : {recommendation.reason.title}")


if __name__ == "__main__":
    app()
