from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from configuration_engine.backend_configuration import BackendConfiguration
from configuration_engine.configuration import Configuration
from configuration_engine.configuration_loader import ConfigurationLoader
from configuration_engine.configuration_paths import (
    configuration_file,
    credentials_file,
    default_configuration_directory,
    profiles_directory,
)
from configuration_engine.credentials import MqttCredentials
from configuration_engine.credentials_loader import CredentialsLoader
from configuration_engine.mqtt_configuration import MqttConfiguration
from configuration_engine.setup_helpers import (
    validate_mqtt_settings,
    write_location_pointer,
)


class FirstRunScreen(ModalScreen[Path | None]):
    """Collect the configuration needed for first application use."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    FirstRunScreen {
        align: center middle;
    }

    #setup-box {
        width: 72;
        height: auto;
        padding: 2 4;
        border: round $accent;
        background: $surface;
    }

    .setup-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .setup-description {
        margin-bottom: 1;
    }

    .setup-label {
        margin-top: 1;
    }

    .setup-error {
        color: $error;
        margin-top: 1;
    }

    .setup-buttons {
        width: 100%;
        height: 3;
        margin-top: 1;
        align-horizontal: right;
    }

    .setup-buttons Button {
        margin-left: 1;
    }

    .setup-single-button {
        width: 100%;
        height: 3;
        margin-top: 1;
        align-horizontal: right;
    }

    .setup-single-button Button {
        margin-left: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()

        self.configuration_directory = default_configuration_directory()

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
        with Vertical(id="setup-box"):
            yield Static(
                id="setup-content",
            )

    def on_mount(self) -> None:
        """Display the first setup step."""

        self.show_directory_step()

    def show_directory_step(self) -> None:
        """Display the configuration-directory step."""

        self.step = 1

        content = self.query_one(
            "#setup-content",
            Static,
        )

        content.update(
            f"""[bold]Configuration Engine — First-Time Setup[/bold]

    Where should Configuration Engine store its files?

    Configuration directory:

    {self.configuration_directory}

    Configuration Engine will store its files in this directory.

    If you choose another location, Configuration Engine will not
    move or copy existing files. You are responsible for moving
    existing files if necessary."""
        )

        self._replace_controls(
            [
                Horizontal(
                    Button(
                        "Change directory",
                        id="change-directory",
                    ),
                    classes="setup-single-button",
                ),
                Horizontal(
                    Button(
                        "Next",
                        id="directory-next",
                        variant="primary",
                    ),
                    classes="setup-buttons",
                ),
            ],
        )

        self.query_one(
            "#change-directory",
            Button,
        ).focus()

    def show_mqtt_step(self) -> None:
        """Display the MQTT configuration step."""

        self.step = 2

        content = self.query_one(
            "#setup-content",
            Static,
        )

        content.update(
            """[bold]Configuration Engine — First-Time Setup[/bold]

    MQTT connection

    Configuration Engine needs access to Zigbee2MQTT."""
        )

        self._replace_controls(
            [
                Label(
                    "MQTT host",
                    classes="setup-label",
                ),
                Input(
                    value=self.mqtt_host,
                    placeholder="e.g. localhost or 192.168.1.24",
                    id="setup-host",
                    classes="debug-key-input",
                ),
                Label(
                    "MQTT port",
                    classes="setup-label",
                ),
                Input(
                    value=self.mqtt_port,
                    id="setup-port",
                ),
                Label(
                    "MQTT username",
                    classes="setup-label",
                ),
                Input(
                    value=self.mqtt_username,
                    placeholder="MQTT username",
                    id="setup-username",
                ),
                Label(
                    "MQTT password",
                    classes="setup-label",
                ),
                Input(
                    value=self.mqtt_password,
                    placeholder="MQTT password",
                    password=True,
                    id="setup-password",
                ),
                Static(
                    "",
                    id="setup-error",
                    classes="setup-error",
                ),
                Horizontal(
                    Button(
                        "Next",
                        id="mqtt-next",
                        variant="primary",
                    ),
                    Button(
                        "Back",
                        id="mqtt-back",
                    ),
                    classes="setup-buttons",
                ),
            ],
        )

        self.query_one(
            "#setup-host",
            Input,
        ).focus()

    def show_confirmation_step(self) -> None:
        """Display the configuration confirmation step."""

        self.step = 3

        content = self.query_one(
            "#setup-content",
            Static,
        )

        content.update(
            f"""[bold]Configuration Engine — Ready[/bold]

    Configuration directory:

    {self.configuration_directory}

    MQTT host:
    {self.mqtt_host}

    MQTT port:
    {self.mqtt_port}

    MQTT username:
    {self.mqtt_username}

    MQTT password:
    ********

    Your password will be stored separately in
    credentials.yaml.

    Files will be created as:

        config.yaml
        credentials.yaml
        profiles\\"""
        )

        self._replace_controls(
            [
                Horizontal(
                    Button(
                        "Save",
                        id="confirmation-save",
                        variant="primary",
                    ),
                    Button(
                        "Back",
                        id="confirmation-back",
                    ),
                    classes="setup-buttons",
                ),
            ],
        )

        self.query_one(
            "#confirmation-save",
            Button,
        ).focus()

    def _replace_controls(
        self,
        widgets: list[Widget],
    ) -> None:
        """Replace the contents of the setup modal."""

        container = self.query_one(
            "#setup-box",
            Vertical,
        )

        children = list(container.children)

        for child in children:
            if child.id != "setup-content":
                child.remove()

        for widget in widgets:
            container.mount(widget)

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:
        """Handle setup buttons."""

        button_id = event.button.id

        if button_id == "change-directory":
            self.change_directory()
            return

        if button_id in (
            "directory-next",
            "mqtt-next",
        ):
            self.next_step()
            return

        if button_id in (
            "mqtt-back",
            "confirmation-back",
        ):
            self.previous_step()
            return

        if button_id == "confirmation-save":
            self.save()
            return

        if button_id == "directory-back":
            self.show_directory_step()
            return

        if button_id == "directory-use":
            self._use_directory()

    def _use_directory(self) -> None:
        """Accept and validate the directory entered by the user."""

        value = self.query_one(
            "#setup-directory",
            Input,
        ).value.strip()

        if not value:
            self.notify(
                "A configuration directory is required.",
                severity="error",
            )
            return

        directory = Path(value)

        if directory.exists():
            if not directory.is_dir():
                self.notify(
                    "The selected path exists but is not a directory.",
                    severity="error",
                )
                return
        elif not directory.parent.exists():
            self.notify(
                "The parent directory does not exist.",
                severity="error",
            )
            return

        self.configuration_directory = directory
        self.show_directory_step()

    def change_directory(self) -> None:
        """Show the directory input."""

        self._replace_controls(
            [
                Static(
                    "[bold]Configuration Engine — First-Time Setup[/bold]\n\n"
                    "Enter the directory where Configuration Engine "
                    "should store its files.",
                    classes="setup-description",
                ),
                Input(
                    value=str(self.configuration_directory),
                    id="setup-directory",
                ),
                Static(
                    "Existing files will not be moved or copied.",
                    classes="setup-description",
                ),
                Horizontal(
                    Button(
                        "Use directory",
                        id="directory-use",
                        variant="primary",
                    ),
                    Button(
                        "Back",
                        id="directory-back",
                    ),
                    classes="setup-buttons",
                ),
            ],
        )

        self.query_one(
            "#setup-directory",
            Input,
        ).focus()

    def next_step(self) -> None:
        """Advance to the next setup step."""

        if self.step == 1:
            self.show_mqtt_step()
            return

        if self.step == 2:
            if not self._read_mqtt_values():
                return

            self.show_confirmation_step()

    def previous_step(self) -> None:
        """Return to the previous setup step."""

        if self.step == 2:
            self.show_directory_step()
            return

        if self.step == 3:
            self.show_mqtt_step()

    def _read_mqtt_values(self) -> bool:
        """Read and validate MQTT settings."""

        host = self.query_one(
            "#setup-host",
            Input,
        ).value.strip()

        port = self.query_one(
            "#setup-port",
            Input,
        ).value.strip()

        username = self.query_one(
            "#setup-username",
            Input,
        ).value.strip()

        password = self.query_one(
            "#setup-password",
            Input,
        ).value

        error = self.query_one(
            "#setup-error",
            Static,
        )

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

    def save(self) -> None:
        """Save the configuration and credentials."""

        try:
            directory = self.configuration_directory

            if not directory.exists():
                directory.mkdir()

            if not directory.is_dir():
                self._show_error("The configuration path is not a directory.")
                return

            profiles_directory(directory).mkdir(
                parents=True,
                exist_ok=True,
            )

            configuration_path = configuration_file(directory)
            credentials_path = credentials_file(directory)

            configuration = Configuration(
                backend=BackendConfiguration(
                    name="zigbee2mqtt",
                ),
                mqtt=MqttConfiguration(
                    host=self.mqtt_host,
                    port=int(self.mqtt_port),
                ),
            )

            credentials = MqttCredentials(
                username=self.mqtt_username,
                password=self.mqtt_password,
            )

            ConfigurationLoader.create(
                configuration_path,
                configuration,
            )

            CredentialsLoader.create(
                credentials_path,
                credentials,
            )

            write_location_pointer(directory)

        except (
            FileExistsError,
            OSError,
            PermissionError,
        ) as exc:
            self._show_error(f"Unable to save configuration: {exc}")
            return

        self.dismiss(directory)

    def _show_error(self, message: str) -> None:
        """Display an error on the current setup step."""

        try:
            error = self.query_one(
                "#setup-error",
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
        """Cancel first-run setup."""

        self.dismiss(None)
