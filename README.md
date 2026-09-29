# Configuration Engine

Configure one device exactly the way you want. Capture that configuration as a profile. Apply it to other similar devices.

Configuration Engine is a deterministic configuration management tool for home automation devices.

Rather than manually configuring every similar device through Zigbee2MQTT, Configuration Engine lets you capture a known-good configuration once and reuse it.

## Current status

Version 0.1.0 is the first public release.

Configuration Engine has been developed and tested on Windows with:

- Home Assistant
- Zigbee2MQTT
- The Mosquitto MQTT broker

Other MQTT brokers or deployment arrangements may work, but they have not been tested as part of this release.

Configuration Engine currently communicates with Zigbee2MQTT through MQTT. It does not replace Zigbee2MQTT or provide a general-purpose device configuration interface.

## What it does

Configuration Engine can:

- Discover devices through Zigbee2MQTT
- Display device information
- Capture a device's current configuration as a profile
- Analyze device configuration
- Compare a device with a profile
- Compare profiles
- Apply a profile to another device
- Verify the resulting configuration
- List available profiles
- Rename profiles
- Delete profiles
- Refresh the device list

The goal is repeatable configuration rather than ad-hoc device editing.

## Requirements

- Windows
- Python 3.14 or newer
- A working Zigbee2MQTT installation
- MQTT access to the Zigbee2MQTT broker

For the 0.1.0 release, the tested environment is Home Assistant using Zigbee2MQTT with the Mosquitto MQTT broker.

## Installation

### Windows

#### Standard installation

1. Install Git for Windows and Python 3.14 or newer.
2. Open PowerShell and change to the directory where you want Configuration Engine installed.

For example:

    cd "D:\Git Projects"

3. Download the installer:

    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/SoundOfMind/configuration_engine/main/bootstrap_ce.ps1" -OutFile ".\bootstrap_ce.ps1"

4. Run the installer:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\bootstrap_ce.ps1"

The installer creates the `configuration_engine` directory in the current directory, creates the Python virtual environment, installs Configuration Engine and its dependencies, and creates a Configuration Engine shortcut on the Windows Desktop.

No administrator privileges are required. The installer does not permanently change the PowerShell execution policy.

#### Development installation

If you want to develop Configuration Engine or create your own variants, clone the repository instead of using the standard installer:

    git clone https://github.com/SoundOfMind/configuration_engine.git

    cd configuration_engine

Create the development virtual environment:

    python -m venv .venv

Install Configuration Engine with the development dependencies:

    python -m pip install -e ".[dev]"

### Linux

#### Standard installation

Clone the repository:

    git clone https://github.com/SoundOfMind/configuration_engine.git

Change to the repository directory:

    cd configuration_engine

Create the virtual environment:

    python3 -m venv .venv

Install Configuration Engine:

    .venv/bin/python -m pip install -e "."

Start Configuration Engine:

    .venv/bin/python -m configuration_engine.tui

#### Development installation

If you want to develop Configuration Engine or create your own variants, use the same setup with the development dependencies:

    .venv/bin/python -m pip install -e ".[dev]"

## Updating an Existing Installation

If you already have a Configuration Engine installation, update it from the repository root (e.g. `D:\Git Projects\configuration_engine`).

### Windows

For a standard installation:

    git pull
    .\.venv\Scripts\python.exe -m pip install -e "."

For a development installation:

    git pull
    .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

### Linux

For a standard installation:

    git pull
    .venv/bin/python -m pip install -e "."

For a development installation:

    git pull
    .venv/bin/python -m pip install -e ".[dev]"

## Starting Configuration Engine

### Windows

For a normal installation, use the Configuration Engine Desktop shortcut.

For a development installation, run:

    .venv\Scripts\python.exe -m configuration_engine.tui

### Linux

From the repository root:

    .venv/bin/python -m configuration_engine.tui

## First-time setup

Start Configuration Engine by double-clicking the CE icon, or with:

    python -m configuration_engine.tui

On first startup, Configuration Engine asks where it should store its configuration files.

The default Windows location is:

    %LOCALAPPDATA%\configuration_engine

You may select another configuration directory during setup.

Configuration Engine then asks for:

- MQTT host
- MQTT port
- MQTT username
- MQTT password

For a typical Home Assistant/Zigbee2MQTT installation, the MQTT credentials can be found in the Zigbee2MQTT configuration. The in-application Help screen provides the specific instructions used by this project for locating those credentials.

If your Home Assistant or Zigbee2MQTT installation is arranged differently, use the appropriate credentials for your environment.

Configuration Engine stores configuration and credentials separately:

    config.yaml
    credentials.yaml
    profiles\

The MQTT password is not stored in `config.yaml`.

The credentials file is protected as read-only by Configuration Engine.

## Using Configuration Engine

The normal workflow is:

1. Configure one device using Zigbee2MQTT.
2. Use Configuration Engine to inspect and analyze the device.
3. Capture the device configuration as a profile.
4. Use that profile as the known-good configuration for similar devices.
5. Apply the profile to another device.
6. Verify the resulting configuration.
7. Make any device-specific adjustments in Zigbee2MQTT.
8. Capture another profile when a useful variation is established.

Configuration Engine does not attempt to replace the normal Zigbee2MQTT interface for individual device settings.

### Profiles

Profiles contain the configuration values that Configuration Engine uses when comparing or applying configurations.

Profiles are intended to be reusable. Give them descriptive names that identify their purpose.

For example, a base profile can represent the configuration you want to use for a particular device model. A second profile can represent a variation for a particular installation or use case.

Profiles are ordinary YAML files and can be backed up or shared.

## Device analysis

The `analyze` operation examines a device and provides recommendations about which properties should be considered part of its configuration.

This is particularly useful when working with a device model that has not previously been encountered by Configuration Engine.

## Applying profiles

Applying a profile changes device configuration through Zigbee2MQTT.

Use care when selecting the target device and profile.

Some device properties may deliberately be preserved rather than changed. For example, Configuration Engine has logic intended to avoid unintentionally changing certain device-specific settings.

After applying a profile, verify the device and make any required device-specific adjustments through Zigbee2MQTT.

## Example profiles

The release includes two example profiles:

- Inovelli VZM31-SN Dimmer Example.yaml
- Inovelli VZM35-SN 3 Speed Fan Control Example.yaml

These examples demonstrate how Configuration Engine represents reusable device configuration as YAML.

## In-application help

Configuration Engine includes help directly in the TUI.

Press `?` to open Help.

Basic navigation:

- Arrow keys - move within the active list
- Enter - select the highlighted item
- Tab / Shift-Tab - switch between Devices and Commands or navigate buttons
- Esc - go back / cancel
- `?` - open Help

Press `R` to refresh the device list after adding or renaming a device in Zigbee2MQTT.

The complete in-application help also contains setup guidance and examples of common workflows.

## Current limitations

Version 0.1.0 is intentionally limited.

- Windows is the only tested operating system.
- The tested environment is Home Assistant with Zigbee2MQTT and Mosquitto.
- Other MQTT brokers and deployment arrangements have not been tested.
- Configuration Engine currently focuses on Zigbee2MQTT.
- Individual device settings are still managed through Zigbee2MQTT.
- Device-specific behavior may require analysis and manual adjustment.
- Additional device models and configuration behavior will continue to be evaluated as the project develops.

## Contributing

Configuration Engine 0.1.0 has been tested on Windows with Home Assistant, Zigbee2MQTT, and the Mosquitto MQTT broker.

Testing and contributions are welcome, particularly from developers who can help expand Configuration Engine beyond the current tested environment.

Areas of interest include:

- macOS and Linux support
- Additional MQTT brokers
- ZHA (Zigbee Home Automation)
- Matter
- Z-Wave
- Additional device models and profiles

If you use Configuration Engine in one of these environments, testing reports and implementation contributions are welcome. The project is being developed so that device ecosystems can be supported through backend/adaptor implementations rather than being tightly coupled to one interface.

## Development

Development dependencies can be installed with:

    python -m pip install -e ".[dev]"

Run the test suite with:

    pytest

Run Ruff:

    ruff check .

Run mypy:

    mypy src

The project uses strict mypy checking.

## License

Configuration Engine is released under the MIT License. See [LICENSE](LICENSE).
