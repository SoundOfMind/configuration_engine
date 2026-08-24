from __future__ import annotations

import shutil
import stat
from pathlib import Path
from typing import ClassVar

import yaml
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from configuration_engine.configuration import Configuration
from configuration_engine.configuration_loader import ConfigurationLoader
from configuration_engine.configuration_paths import (
    configuration_file,
    credentials_file,
)
from configuration_engine.credentials import MqttCredentials
from configuration_engine.credentials_loader import CredentialsLoader
from configuration_engine.mqtt_configuration import MqttConfiguration
from configuration_engine.setup_helpers import (
    validate_mqtt_settings,
    write_location_pointer,
)


class SettingsScreen(ModalScreen[Path | None]):
    """Edit the active configuration settings."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-box {
        width: 76;
        height: auto;
        max-height: 90%;
        padding: 2 4;
        border: round $accent;
        background: $surface;
    }

    .settings-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .settings-description {
        margin-bottom: 1;
    }

    .settings-label {
        margin-top: 1;
    }

    .settings-error {
        color: $error;
        margin-top: 1;
    }

    .settings-buttons {
        width: 100%;
        height: 3;
        margin-top: 1;
        align-horizontal: right;
    }

    .settings-buttons Button {
        margin-left: 1;
    }

    .settings-single-button {
        width: 100%;
        height: 3;
        margin-top: 1;
        align-horizontal: right;
    }
    """

    def __init__(self, configuration_directory: Path) -> None:
        super().__init__()

        self.configuration_directory = configuration_directory
        self.original_configuration_directory = configuration_directory

        self.mqtt_host = ""
        self.mqtt_port = "1883"
        self.mqtt_username = ""
        self.mqtt_password = ""

        self.step = 1

    def on_key(self, event: events.Key) -> None:
        """Handle keys that the terminal doesn't translate to text."""

        if event.key != "decimal":
            return

        if isinstance(self.focused, Input):
            self.focused.insert_text_at_cursor(".")
            event.stop()

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-box"):
            yield Static(id="settings-content")

    def on_mount(self) -> None:
        """Load the active configuration and display the first step."""

        try:
            configuration = ConfigurationLoader.load(
                configuration_file(self.configuration_directory),
            )

            self.mqtt_host = configuration.mqtt.host or ""
            self.mqtt_port = str(configuration.mqtt.port)

            credentials_path = credentials_file(self.configuration_directory)

            credentials = CredentialsLoader.load(credentials_path)
            self.mqtt_username = credentials.username or ""
            self.mqtt_password = credentials.password or ""

        except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
            self.notify(
                f"Unable to load settings: {exc}",
                severity="error",
            )
            self.dismiss(None)
            return

        self.show_directory_step()

    def show_directory_step(self) -> None:
        """Display the configuration-directory step."""

        self.step = 1

        content = self.query_one(
            "#settings-content",
            Static,
        )

        if self.configuration_directory == self.original_configuration_directory:
            directory_message = "The active configuration directory will not change."
        else:
            directory_message = "The Configuration Engine files will be moved to this directory."

        content.update(
            f"""[bold]Configuration Engine — Settings[/bold]

    Where should Configuration Engine store its files?

    Configuration directory:

    {self.configuration_directory}

    {directory_message}"""
        )

        self._replace_controls(
            [
                Horizontal(
                    Button(
                        "Change directory",
                        id="settings-directory-change",
                    ),
                    classes="settings-single-button",
                ),
                Horizontal(
                    Button(
                        "Next",
                        id="settings-directory-next",
                        variant="primary",
                    ),
                    Button(
                        "Cancel",
                        id="settings-directory-back",
                    ),
                    classes="settings-buttons",
                ),
            ],
        )

        self.query_one(
            "#settings-directory-next",
            Button,
        ).focus()

    def change_directory(self) -> None:
        """Display the directory editor."""

        self._replace_controls(
            [
                Static(
                    "Enter the directory where Configuration Engine should store its files.",
                    classes="settings-description",
                ),
                Label(
                    "Configuration directory",
                    classes="settings-label",
                ),
                Input(
                    value=str(self.configuration_directory),
                    id="settings-directory-input",
                ),
                Static(
                    "A new directory must have an existing parent and must be "
                    "empty if it already exists.",
                    classes="settings-description",
                ),
                Static(
                    "",
                    id="settings-error",
                    classes="settings-error",
                ),
                Horizontal(
                    Button(
                        "Use directory",
                        id="settings-directory-use",
                        variant="primary",
                    ),
                    Button(
                        "Cancel",
                        id="settings-directory-edit-back",
                    ),
                    classes="settings-buttons",
                ),
            ],
        )

        self.query_one(
            "#settings-directory-input",
            Input,
        ).focus()

    def _use_directory(self) -> None:
        """Accept and validate the directory entered by the user."""

        value = self.query_one(
            "#settings-directory-input",
            Input,
        ).value.strip()

        if not value:
            self._show_error("Configuration directory is required.")
            return

        directory = Path(value)

        try:
            self._validate_move_destination(
                self.original_configuration_directory,
                directory,
            )
        except (OSError, ValueError) as exc:
            self._show_error(str(exc))
            return

        self.configuration_directory = directory
        self.show_directory_step()

    def show_mqtt_step(self) -> None:
        """Display the MQTT configuration step."""

        self.step = 2

        content = self.query_one(
            "#settings-content",
            Static,
        )

        content.update(
            """[bold]Configuration Engine — Settings[/bold]

    MQTT connection

    These values control how Configuration Engine
    connects to Zigbee2MQTT."""
        )

        self._replace_controls(
            [
                Label(
                    "MQTT host",
                    classes="settings-label",
                ),
                Input(
                    value=self.mqtt_host,
                    id="settings-host",
                ),
                Label(
                    "MQTT port",
                    classes="settings-label",
                ),
                Input(
                    value=self.mqtt_port,
                    id="settings-port",
                ),
                Label(
                    "MQTT username",
                    classes="settings-label",
                ),
                Input(
                    value=self.mqtt_username,
                    id="settings-username",
                ),
                Label(
                    "MQTT password",
                    classes="settings-label",
                ),
                Input(
                    value=self.mqtt_password,
                    password=True,
                    id="settings-password",
                ),
                Static(
                    "",
                    id="settings-error",
                    classes="settings-error",
                ),
                Horizontal(
                    Button(
                        "Next",
                        id="settings-mqtt-next",
                        variant="primary",
                    ),
                    Button(
                        "Back",
                        id="settings-mqtt-back",
                    ),
                    classes="settings-buttons",
                ),
            ],
        )

        self.query_one(
            "#settings-host",
            Input,
        ).focus()

    def show_confirmation_step(self) -> None:
        """Display the settings confirmation step."""

        self.step = 3

        content = self.query_one(
            "#settings-content",
            Static,
        )

        if self.configuration_directory != self.original_configuration_directory:
            directory_message = "The Configuration Engine files will be moved to the new directory."
        else:
            directory_message = "The active configuration directory will not change."

        content.update(
            f"""[bold]Configuration Engine — Confirm Changes[/bold]

    Configuration directory:

    {self.configuration_directory}

    {directory_message}

    MQTT host:
    {self.mqtt_host}

    MQTT port:
    {self.mqtt_port}

    MQTT username:
    {self.mqtt_username}

    MQTT password:
    ********

    Press Save to apply these settings."""
        )

        self._replace_controls(
            [
                Horizontal(
                    Button(
                        "Save",
                        id="settings-save",
                        variant="primary",
                    ),
                    Button(
                        "Back",
                        id="settings-confirmation-back",
                    ),
                    classes="settings-buttons",
                ),
            ],
        )

        self.query_one(
            "#settings-save",
            Button,
        ).focus()

    def _replace_controls(self, widgets: list[Widget]) -> None:
        """Replace the controls in the Settings modal."""

        container = self.query_one(
            "#settings-box",
            Vertical,
        )

        children = list(container.children)

        for child in children:
            if child.id != "settings-content":
                child.remove()

        for widget in widgets:
            container.mount(widget)

    def _read_mqtt_values(self) -> bool:
        """Read and validate MQTT settings."""

        host = self.query_one("#settings-host", Input).value.strip()
        port = self.query_one("#settings-port", Input).value.strip()
        username = self.query_one("#settings-username", Input).value.strip()
        password = self.query_one("#settings-password", Input).value

        error = self.query_one("#settings-error", Static)
        error.update("")

        try:
            settings = validate_mqtt_settings(
                host,
                port,
                username,
                password,
            )
        except ValueError as exc:
            error.update(str(exc))
            return False

        self.mqtt_host = settings.host
        self.mqtt_port = str(settings.port)
        self.mqtt_username = settings.username
        self.mqtt_password = settings.password

        return True

    def next_step(self) -> None:
        """Advance to the next Settings step."""

        if self.step == 1:
            self.show_mqtt_step()
            return

        if self.step == 2:
            if not self._read_mqtt_values():
                return

            self.show_confirmation_step()

    def previous_step(self) -> None:
        """Return to the previous Settings step."""

        if self.step == 2:
            self.show_directory_step()
            return

        if self.step == 3:
            self.show_mqtt_step()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Settings buttons."""

        button_id = event.button.id

        if button_id == "settings-directory-back":
            self.action_cancel()
            return

        if button_id == "settings-directory-change":
            self.change_directory()
            return

        if button_id == "settings-directory-next":
            self.next_step()
            return

        if button_id == "settings-directory-edit-back":
            self.show_directory_step()
            return

        if button_id == "settings-directory-use":
            self._use_directory()
            return

        if button_id == "settings-mqtt-back":
            self.previous_step()
            return

        if button_id == "settings-mqtt-next":
            self.next_step()
            return

        if button_id == "settings-confirmation-back":
            self.previous_step()
            return

        if button_id == "settings-save":
            self.save()

    def _remove_old_configuration_directory(
        self,
        directory: Path,
    ) -> None:
        """Remove the old configuration directory after relocation."""

        if not directory.exists():
            return

        entries = list(directory.iterdir())

        if entries:
            raise OSError(f"Old configuration directory is not empty: {directory}")

        directory.rmdir()

    def save(self) -> None:
        """Persist settings and relocate the configuration when requested."""

        source = self.original_configuration_directory.resolve()
        destination = self.configuration_directory.resolve()
        moved = source != destination

        try:
            if moved:
                self._validate_move_destination(source, destination)
                self._move_configuration(source, destination)

            self._save_configuration(destination)
            write_location_pointer(destination)

        except (
            OSError,
            PermissionError,
            TypeError,
            ValueError,
            yaml.YAMLError,
        ) as exc:
            if moved:
                try:
                    self._move_configuration(destination, source)
                except OSError as rollback_exc:
                    self.notify(
                        f"Unable to save settings: {exc}. Rollback also failed: {rollback_exc}",
                        severity="error",
                    )
                    return

            self._show_error(f"Unable to save settings: {exc}")
            return

        if moved:
            try:
                self._remove_old_configuration_directory(source)
            except OSError as exc:
                self.notify(
                    f"Settings saved, but the old configuration directory "
                    f"could not be removed: {exc}",
                    severity="warning",
                )

        self.dismiss(destination)

    def _save_configuration(self, directory: Path) -> None:
        """Save MQTT configuration and credentials."""

        configuration_path = configuration_file(directory)
        credentials_path = credentials_file(directory)

        old_configuration = ConfigurationLoader.load(
            configuration_path,
        )

        mqtt = MqttConfiguration(
            host=self.mqtt_host,
            port=int(self.mqtt_port),
        )

        configuration = Configuration(
            backend=old_configuration.backend,
            mqtt=mqtt,
        )

        ConfigurationLoader.save(
            configuration_path,
            configuration,
        )

        credentials = MqttCredentials(
            username=self.mqtt_username,
            password=self.mqtt_password,
        )

        CredentialsLoader.save(
            credentials_path,
            credentials,
        )

    def _validate_move_destination(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        """Validate a configuration relocation destination."""

        source = source.resolve()
        destination = destination.resolve()

        if source == destination:
            return

        if destination.exists():
            if not destination.is_dir():
                raise ValueError("The selected configuration path exists but is not a directory.")

            entries: list[Path] = []

            for entry in destination.iterdir():
                if entry.name != "location.yaml":
                    entries.append(entry)

            if entries:
                raise ValueError("The selected directory is not empty.")
        elif not destination.parent.exists():
            raise ValueError(
                "The parent directory of the selected configuration directory does not exist."
            )

        if destination.is_relative_to(source):
            raise ValueError(
                "The new configuration directory cannot be inside the "
                "current configuration directory."
            )

    def _move_configuration(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        """Move the Configuration Engine payload to another directory."""

        source = source.resolve()
        destination = destination.resolve()

        if source == destination:
            return

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        names = (
            "config.yaml",
            "config.yaml.lock",
            "config.yaml.bak",
            "credentials.yaml",
            "credentials.yaml.lock",
            "credentials.yaml.bak",
            "profiles",
        )

        moved: list[tuple[Path, Path]] = []

        try:
            for name in names:
                source_path = source / name

                if not source_path.exists():
                    continue

                destination_path = destination / name

                if destination_path.exists():
                    raise FileExistsError(f"Destination already contains {name}.")

                if source_path.is_file():
                    original_mode = stat.S_IMODE(
                        source_path.stat().st_mode,
                    )

                    source_path.chmod(
                        original_mode | stat.S_IWUSR,
                    )

                    try:
                        shutil.move(
                            str(source_path),
                            str(destination_path),
                        )
                    except OSError:
                        if source_path.exists():
                            source_path.chmod(original_mode)

                        raise

                    if destination_path.exists():
                        destination_path.chmod(original_mode)

                else:
                    shutil.move(
                        str(source_path),
                        str(destination_path),
                    )

                moved.append(
                    (
                        destination_path,
                        source_path,
                    )
                )

        except OSError:
            for moved_path, original_path in reversed(moved):
                if not moved_path.exists():
                    continue

                original_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                if moved_path.is_file():
                    original_mode = stat.S_IMODE(
                        moved_path.stat().st_mode,
                    )

                    moved_path.chmod(
                        original_mode | stat.S_IWUSR,
                    )

                    shutil.move(
                        str(moved_path),
                        str(original_path),
                    )

                    original_path.chmod(original_mode)

                else:
                    shutil.move(
                        str(moved_path),
                        str(original_path),
                    )

            if destination.exists():
                entries = list(destination.iterdir())

                if not entries:
                    destination.rmdir()

            raise

    def _show_error(self, message: str) -> None:
        """Display a Settings error."""

        try:
            error = self.query_one(
                "#settings-error",
                Static,
            )
        except NoMatches:
            self.notify(
                message,
                severity="error",
            )
            return

        error.update(message)

    def action_cancel(self) -> None:
        """Cancel Settings without changing anything."""

        self.dismiss(None)
