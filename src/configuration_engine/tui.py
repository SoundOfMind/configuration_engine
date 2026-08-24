from __future__ import annotations

import asyncio
from enum import Enum, IntEnum, auto
from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    DataTable,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from configuration_engine.configuration_engine import ConfigurationEngine
from configuration_engine.configuration_paths import (
    active_configuration_directory,
    configuration_file,
    profiles_directory,
)
from configuration_engine.device_summary import DeviceSummary
from configuration_engine.first_run import FirstRunScreen
from configuration_engine.profile_difference import ProfileDifference
from configuration_engine.profile_repository import ProfileRepository
from configuration_engine.settings import SettingsScreen
from configuration_engine.startup import StartupScreen


class Command(IntEnum):
    PROFILE_LIST = 0
    PROFILES_COMPARE = 1
    DEVICE_INFO = 2
    DEVICE_SNAPSHOT = 3
    DEVICE_ANALYZE = 4
    DEVICE_CAPTURE = 5
    DEVICE_COMPARE = 6
    DEVICE_APPLY = 7
    PROGRAM_SETUP = 8


class CaptureStep(Enum):
    """Current step in the capture workflow."""

    PROFILE_NAME = auto()
    SOURCE_DEVICE = auto()
    READY = auto()


class ConfigurationApp(App[None]):
    """Interactive Configuration Engine terminal application."""

    TITLE = "Configuration Engine"
    CSS_PATH = "tui.tcss"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "back", "Back"),
        Binding("question_mark", "help", "Help"),
        Binding("r", "refresh_devices", "Refresh"),
        Binding("R", "refresh_devices", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()

        self.operation_failed = False
        self.help_returns_to_startup = False
        self.help_previous_workspace: list[str] = []
        self.help_previous_focus: str | None = None
        self.help_previous_title: str | None = None
        self.help_previous_instruction: str | None = None
        self.operation_in_progress = False
        self.devices: list[DeviceSummary] = []
        self.device_status: dict[str, str] = {}
        self.active_command: Command | None = None
        self.profile_rename_active = False
        self.profile_delete_active = False

        self.configuration_directory = active_configuration_directory()

        self.capture_step = CaptureStep.PROFILE_NAME
        self.capture_profile_name = ""
        self.capture_device: str | None = None

        self.snapshot_device: str | None = None

        self.compare_device: str | None = None
        self.compare_profile: str | None = None
        self.profile_list_profile: str | None = None
        self.profile_compare_first: str | None = None
        self.profile_compare_second: str | None = None
        self.profile_compare_show_differences = False

        self.apply_device: str | None = None
        self.apply_profile: str | None = None

    def device_status_class(self, device_name: str) -> str:
        """Return the CSS class representing a device's session status."""

        status = self.device_status.get(device_name)

        if status == "success":
            return "device-success"

        if status == "unavailable":
            return "device-unavailable"

        return ""

    def configuration_path(self) -> Path:
        """Return the application's configuration file path."""

        return configuration_file(self.configuration_directory)

    def profile_repository(self) -> ProfileRepository:
        """Return the application's profile repository."""

        return ProfileRepository(
            profiles_directory(self.configuration_directory),
        )

    def hide_navigation_chrome(self) -> None:
        """Hide normal navigation decorations while a modal is open."""

        self.query_one(
            "#devices",
        ).query_one(
            ".pane-title",
            Static,
        ).display = False

        self.query_one(
            "#command",
        ).query_one(
            ".pane-title",
            Static,
        ).display = False

        self.query_one(
            "#devices-instruction",
            Static,
        ).display = False

        self.query_one(
            "#instruction",
            Static,
        ).display = False

    def show_navigation_chrome(self) -> None:
        """Restore normal navigation decorations after a modal closes."""

        self.query_one(
            "#devices",
        ).query_one(
            ".pane-title",
            Static,
        ).display = True

        self.query_one(
            "#command",
        ).query_one(
            ".pane-title",
            Static,
        ).display = True

        self.query_one(
            "#devices-instruction",
            Static,
        ).display = True

        self.query_one(
            "#instruction",
            Static,
        ).display = True

    def make_device_list_item(
        self,
        number: int,
        device: DeviceSummary,
    ) -> ListItem:
        """Create a device list item with its current session status."""

        return ListItem(
            Label(f"{number:>2}  {device.friendly_name}"),
            classes=self.device_status_class(device.friendly_name),
        )

    def mark_device_success(self, device_name: str) -> None:
        """Mark a device as successfully contacted this session."""

        self.device_status[device_name] = "success"
        self.refresh_device_list_item(device_name)

    def mark_device_unavailable(self, device_name: str) -> None:
        """Mark a device as unavailable or unresponsive."""

        self.device_status[device_name] = "unavailable"
        self.refresh_device_list_item(device_name)

    def refresh_device_list_item(self, device_name: str) -> None:
        """Update the displayed status color for a device."""

        device_list = self.query_one(
            "#device-list",
            ListView,
        )

        for index, device in enumerate(
            self.devices,
            start=1,
        ):
            if device.friendly_name != device_name:
                continue

            if index - 1 >= len(device_list.children):
                return

            item = device_list.children[index - 1]

            if not isinstance(item, ListItem):
                return

            item.remove_class("device-success")
            item.remove_class("device-unavailable")

            status_class = self.device_status_class(device_name)

            if status_class:
                item.add_class(status_class)

            return

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main"):
            with Vertical(id="devices"):
                yield Static(
                    "Devices",
                    classes="pane-title",
                )

                yield ListView(
                    id="device-list",
                )

                yield Static(
                    "Tab: switch window   R: refresh",
                    id="devices-instruction",
                )

            with Vertical(id="command"):
                yield Static(
                    "Command",
                    classes="pane-title",
                )

                yield Static(
                    "",
                    id="command-title",
                    markup=True,
                )

                with Vertical(id="command-workspace"):
                    yield ListView(
                        id="command-list",
                    )

                    with VerticalScroll(id="help-view"):
                        yield Static(
                            "",
                            id="help-content",
                        )

                    with Vertical(id="capture-form"):
                        yield Input(
                            placeholder="Profile name",
                            id="capture-profile",
                        )

                        yield Static("From")

                        yield Static(
                            "No device selected",
                            id="capture-device-value",
                        )

                    with Vertical(id="device-selector"):
                        yield ListView(
                            id="capture-device-list",
                        )

                    with Vertical(id="profile-selector"):
                        yield ListView(
                            id="compare-profile-list",
                        )

                    with Vertical(id="profile-list"):
                        yield ListView(
                            id="profile-list-view",
                        )

                    with Vertical(id="profile-view"):
                        with VerticalScroll(id="profile-content-view"):
                            yield Static(
                                "",
                                id="profile-content",
                            )

                        yield Input(
                            placeholder="New profile name",
                            id="profile-rename-input",
                        )

                    with VerticalScroll(id="snapshot-view"):
                        yield Static(
                            "",
                            id="snapshot-content",
                        )

                    yield DataTable(
                        id="compare-view",
                    )

                yield Static(
                    "",
                    id="instruction",
                )

    def update_command_title(
        self,
        command: str | None = None,
        device: str | None = None,
        profile: str | None = None,
    ) -> None:
        """Update the command and context displayed at the top of the pane."""

        title = self.query_one(
            "#command-title",
            Static,
        )

        if command is None:
            title.update("")
            return

        lines = [
            f"Command: [cyan]{command.replace('_', ' ').capitalize()}[/cyan]",
        ]

        if command == Command.PROFILES_COMPARE.name:
            if device is not None and profile is not None:
                lines.append(f"Profiles: [cyan]{device}[/cyan] vs [cyan]{profile}[/cyan]")
            elif device is not None:
                lines.append(f"Profile: [cyan]{device}[/cyan]")

        elif device is not None:
            if profile is None:
                lines.append(f"Device: [cyan]{device}[/cyan]")
            elif command == Command.DEVICE_COMPARE.name:
                lines.append(f"Device: [cyan]{device}[/cyan] vs Profile: [cyan]{profile}[/cyan]")
            elif command == Command.DEVICE_APPLY.name:
                lines.append(
                    f"Device: [cyan]{device}[/cyan] written from Profile: [cyan]{profile}[/cyan]"
                )
            else:
                lines.append(f"Device: [cyan]{device}[/cyan]")

        title.update("\n".join(lines))

    def update_instruction(
        self,
        message: str,
    ) -> None:
        """Update the instruction at the bottom of the command pane."""

        self.query_one(
            "#instruction",
            Static,
        ).update(message)

    def update_capture_instruction(
        self,
        message: str | None = None,
    ) -> None:
        """Update the instruction for the current capture step."""

        if message is not None:
            self.update_instruction(message)
            return

        messages = {
            CaptureStep.PROFILE_NAME: ("Enter the profile name, then press Enter."),
            CaptureStep.SOURCE_DEVICE: ("Select the source device, then press Enter."),
            CaptureStep.READY: "Press Enter to capture.",
        }

        self.update_instruction(messages[self.capture_step])

    def show_operation_failure(
        self,
        message: str,
    ) -> None:
        """Display an operation failure and keep Esc available to return."""

        self.operation_failed = True
        self.update_instruction(f"{message}\nPress Esc to return.")

    async def _populate_profile_list(self) -> bool:
        """Populate the profile list from the repository."""

        repository = self.profile_repository()

        profile_list = self.query_one(
            "#profile-list-view",
            ListView,
        )

        await profile_list.clear()

        profiles = repository.list()

        if not profiles:
            self.update_instruction(
                "No profiles found. Press Esc to return.",
            )
            profile_list.display = True
            return False

        for profile_name in profiles:
            await profile_list.append(
                ListItem(Label(profile_name)),
            )

        profile_list.index = 0
        profile_list.focus()

        return True

    async def start_profile_list(self) -> None:
        """Start the Profile List workflow."""

        self.active_command = Command.PROFILE_LIST
        self.profile_list_profile = None

        self.query_one(
            "#command-profile_list",
            ListItem,
        ).add_class("active-command")

        self.query_one("#command-list").display = False
        self.query_one("#command-title").display = True

        self.query_one("#profile-list").display = True
        self.query_one("#profile-view").display = False

        self.update_command_title(
            self.active_command.name.replace("_", " ").lower(),
        )

        if not await self._populate_profile_list():
            return

        self.update_instruction(
            "Select a profile, then press Enter.",
        )

    async def start_profiles_compare(self) -> None:
        """Start the Profiles Compare workflow."""

        self.active_command = Command.PROFILES_COMPARE

        self.profile_compare_first = None
        self.profile_compare_second = None
        self.profile_compare_show_differences = False
        self.profile_compare_full_closed = False

        self.query_one(
            "#command-profiles_compare",
            ListItem,
        ).add_class("active-command")

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#profile-list").display = False
        self.query_one("#profile-view").display = False
        self.query_one("#snapshot-view").display = False
        self.query_one("#compare-view").display = False

        self.update_command_title(
            self.active_command.name.replace("_", " ").lower(),
        )

        await self._show_profile_selector()

    def show_profile(self) -> None:
        """Display the selected profile."""

        if self.profile_list_profile is None:
            return

        repository = self.profile_repository()

        try:
            profile = repository.read(
                self.profile_list_profile,
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self.show_operation_failure(
                f"Unable to read profile: {exc}",
            )
            return

        rename_input = self.query_one(
            "#profile-rename-input",
            Input,
        )

        rename_input.value = ""
        rename_input.display = False
        self.profile_rename_active = False
        self.profile_delete_active = False

        lines: list[str] = [
            f"Profile: {self.profile_list_profile}",
        ]

        if profile.vendor is not None:
            lines.append(
                f"Vendor: {profile.vendor}",
            )

        if profile.model is not None:
            lines.append(
                f"Model: {profile.model}",
            )

        lines.extend(
            [
                "",
                "Properties",
                "----------",
            ]
        )

        for property_name in sorted(profile.values):
            lines.append(
                f"{property_name}: {profile.values[property_name]}",
            )

        content = self.query_one(
            "#profile-content",
            Static,
        )

        content.update(
            "\n".join(lines),
        )

        self.query_one("#profile-list").display = False
        self.query_one("#profile-view").display = True

        self.update_instruction(
            "N: Rename   D: Delete   Esc: Back",
        )

    def show_profiles_compare(self) -> None:
        """Display the complete comparison of two profiles."""

        if self.profile_compare_first is None:
            return

        if self.profile_compare_second is None:
            return

        repository = self.profile_repository()

        try:
            first_profile = repository.read(
                self.profile_compare_first,
            )

            second_profile = repository.read(
                self.profile_compare_second,
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self.show_operation_failure(
                f"Unable to read profiles: {exc}",
            )
            return

        property_names = sorted(first_profile.values.keys() | second_profile.values.keys())

        table = self.query_one(
            "#compare-view",
            DataTable,
        )

        table.clear(columns=True)

        table.add_column(
            "Property",
            width=32,
        )

        table.add_column(
            self.profile_compare_first,
            width=30,
        )

        table.add_column(
            self.profile_compare_second,
            width=30,
        )

        for property_name in property_names:
            first_value = first_profile.values.get(
                property_name,
                "",
            )

            second_value = second_profile.values.get(
                property_name,
                "",
            )

            table.add_row(
                property_name,
                str(first_value),
                str(second_value),
            )

        self.query_one(
            "#profile-selector",
            Vertical,
        ).display = False

        self.profile_compare_show_differences = False
        self.profile_compare_full_closed = False

        table.display = True
        table.focus()

        self.update_instruction(
            "Press Esc to close. Then Enter for differences or Esc to exit.",
        )

    def show_profile_differences(self) -> None:
        """Display only the differences between two profiles."""

        if self.profile_compare_first is None:
            return

        if self.profile_compare_second is None:
            return

        repository = self.profile_repository()

        try:
            first_profile = repository.read(
                self.profile_compare_first,
            )

            second_profile = repository.read(
                self.profile_compare_second,
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self.show_operation_failure(
                f"Unable to read profiles: {exc}",
            )
            return

        difference = first_profile.compare(
            second_profile,
        )

        table = self.query_one(
            "#compare-view",
            DataTable,
        )

        table.clear(columns=True)

        table.add_column(
            "Property",
            width=32,
        )

        table.add_column(
            self.profile_compare_first,
            width=30,
        )

        table.add_column(
            self.profile_compare_second,
            width=30,
        )

        if difference.is_empty:
            table.add_row(
                "Profiles match.",
                "",
                "",
            )
        else:
            for item in difference.differences:
                table.add_row(
                    item.property_name,
                    str(item.current_value),
                    str(item.desired_value),
                )

        self.profile_compare_show_differences = True
        self.profile_compare_full_closed = False

        table.display = True
        table.focus()

        self.update_instruction(
            "Differences. Press Esc to return.",
        )

    def start_capture(self) -> None:
        """Start the Capture command workflow."""

        self.active_command = Command.DEVICE_CAPTURE

        self.query_one(
            "#command-device_capture",
            ListItem,
        ).add_class("active-command")

        self.capture_step = CaptureStep.PROFILE_NAME
        self.capture_profile_name = ""
        self.capture_device = None

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#capture-form").display = True

        self.query_one("#device-selector").display = False

        self.query_one("#profile-selector").display = False

        self.query_one("#snapshot-view").display = False

        self.query_one("#compare-view").display = False

        self.update_command_title(self.active_command.name)

        self.query_one(
            "#capture-device-value",
            Static,
        ).update("No device selected")

        profile_input = self.query_one(
            "#capture-profile",
            Input,
        )

        profile_input.value = ""
        profile_input.focus()

        self.update_capture_instruction()

    async def capture_profile(self) -> None:
        """Capture the selected device and save the profile."""

        if self.capture_device is None:
            return

        self.update_capture_instruction("Please wait...")
        await asyncio.sleep(0)

        self.operation_in_progress = True

        try:
            engine = ConfigurationEngine.from_file(self.configuration_path())

            profile = await asyncio.to_thread(
                engine.capture,
                self.capture_device,
            )

            self.mark_device_success(self.capture_device)

            repository = self.profile_repository()

            repository.write(
                self.capture_profile_name,
                profile,
            )

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.mark_device_unavailable(self.capture_device)
            self.show_operation_failure(f"Capture failed: {exc}")
            return

        finally:
            self.operation_in_progress = False

        self.capture_step = CaptureStep.READY

        self.update_capture_instruction(
            f'Profile "{self.capture_profile_name}" captured successfully.\nPress Esc to return.'
        )

    async def _show_device_selector(self) -> None:
        """Populate and display the shared device selector."""

        selector = self.query_one(
            "#capture-device-list",
            ListView,
        )

        await selector.clear()

        for device in self.devices:
            await selector.append(
                ListItem(Label(device.friendly_name)),
            )

        selector.display = True

        if self.devices:
            selector.index = 0

        selector.focus()

    async def show_capture_device_selector(
        self,
    ) -> None:
        """Show the device selector for capture."""

        await self._show_device_selector()

        self.query_one("#capture-form").display = False
        self.query_one("#device-selector").display = True

    async def _show_profile_selector(self) -> bool:
        """Populate and display the shared profile selector."""

        selector = self.query_one(
            "#compare-profile-list",
            ListView,
        )

        await selector.clear()

        repository = self.profile_repository()
        profiles = repository.list()

        if not profiles:
            self.update_instruction(
                "No profiles found. Press Esc to return.",
            )
            return False

        for profile_name in profiles:
            await selector.append(
                ListItem(Label(profile_name)),
            )

        self.query_one(
            "#device-selector",
            Vertical,
        ).display = False

        self.query_one(
            "#profile-selector",
            Vertical,
        ).display = True

        selector.index = 0
        selector.focus()

        self.update_instruction(
            "Select the profile, then press Enter.",
        )

        return True

    async def start_snapshot(self) -> None:
        """Start the Snapshot command workflow."""

        self.active_command = Command.DEVICE_SNAPSHOT
        self.snapshot_device = None

        self.query_one(
            "#command-device_snapshot",
            ListItem,
        ).add_class("active-command")

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#capture-form").display = False

        self.query_one("#device-selector").display = True

        self.query_one("#profile-selector").display = False

        self.query_one("#snapshot-view").display = False

        self.query_one("#compare-view").display = False

        self.update_command_title(self.active_command.name)

        self.update_instruction("Select the device, then press Enter.")

        await self._show_device_selector()

    async def show_snapshot(self) -> None:
        """Capture and display the current snapshot."""

        if self.snapshot_device is None:
            return

        self.update_instruction("Please wait...")
        await asyncio.sleep(0)

        self.operation_in_progress = True

        try:
            engine = ConfigurationEngine.from_file(self.configuration_path())

            snapshot = await asyncio.to_thread(
                engine.snapshot,
                self.snapshot_device,
            )

            self.mark_device_success(self.snapshot_device)

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.mark_device_unavailable(self.snapshot_device)
            self.show_operation_failure(f"Snapshot failed: {exc}")
            return

        finally:
            self.operation_in_progress = False

        lines = [
            f"Backend : {snapshot.backend}",
            f"Device  : {snapshot.device_id}",
        ]

        if snapshot.model is not None:
            lines.append(f"Model   : {snapshot.model}")

        lines.extend(
            [
                "Properties",
                "----------",
            ]
        )

        for property_name in sorted(snapshot.values):
            lines.append(f"{property_name:<28} {snapshot.values[property_name]}")

        output_view = self.query_one(
            "#snapshot-view",
            VerticalScroll,
        )

        content = self.query_one(
            "#snapshot-content",
            Static,
        )

        content.update("\n".join(lines))

        output_view.display = True
        output_view.scroll_home(animate=False)
        output_view.focus()

        self.update_instruction("Press Esc to return.")

    async def start_info(self) -> None:
        """Start the Info command workflow."""

        self.active_command = Command.DEVICE_INFO
        self.snapshot_device = None

        self.query_one(
            "#command-device_info",
            ListItem,
        ).add_class("active-command")

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#capture-form").display = False

        self.query_one("#device-selector").display = True

        self.query_one("#profile-selector").display = False

        self.query_one("#snapshot-view").display = False

        self.query_one("#compare-view").display = False

        self.update_command_title(self.active_command.name)

        self.update_instruction("Select the device, then press Enter.")

        await self._show_device_selector()

    async def show_info(self) -> None:
        """Display device information."""

        if self.snapshot_device is None:
            return

        self.update_instruction("Please wait...")
        await asyncio.sleep(0)

        self.operation_in_progress = True

        try:
            engine = ConfigurationEngine.from_file(self.configuration_path())

            info = await asyncio.to_thread(
                engine.info,
                self.snapshot_device,
            )

            definition = await asyncio.to_thread(
                engine.definition,
                self.snapshot_device,
            )

            self.mark_device_success(self.snapshot_device)

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.mark_device_unavailable(self.snapshot_device)
            self.show_operation_failure(f"Info failed: {exc}")
            return

        finally:
            self.operation_in_progress = False

        supported = "Yes" if info.supported else "No"
        interview = info.interview_state or "Unknown"
        interview = interview.capitalize()

        lines = [
            f"Description  : {definition.description}",
            f"Manufacturer : {info.manufacturer}",
            f"Model        : {info.model_id}",
            f"Firmware     : {info.firmware or 'Unknown'}",
            "",
            f"IEEE Address    : {info.ieee_address}",
            f"Network Address : {info.network_address}",
            f"Power Source    : {info.power_source}",
            f"Type            : {info.type}",
            f"Supported       : {supported}",
            f"OTA Support     : {'Yes' if definition.supports_ota else 'No'}",
            f"Interview       : {interview}",
        ]

        output_view = self.query_one(
            "#snapshot-view",
            VerticalScroll,
        )

        content = self.query_one(
            "#snapshot-content",
            Static,
        )

        content.update("\n".join(lines))

        output_view.display = True
        output_view.scroll_home(animate=False)
        output_view.focus()

        self.update_instruction("Press Esc to return.")

    async def show_analyze(self) -> None:
        """Display device analysis."""

        if self.snapshot_device is None:
            return

        self.update_instruction("Please wait...")
        await asyncio.sleep(0)

        self.operation_in_progress = True

        try:
            engine = ConfigurationEngine.from_file(self.configuration_path())

            analysis = await asyncio.to_thread(
                engine.analyze,
                self.snapshot_device,
            )

            self.mark_device_success(self.snapshot_device)

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.mark_device_unavailable(self.snapshot_device)
            self.show_operation_failure(f"Analyze failed: {exc}")
            return

        finally:
            self.operation_in_progress = False

        lines = []

        if analysis.model:
            lines.append(f"Model: {analysis.model}")

        lines.extend(
            [
                "Recommendations",
                "---------------",
            ]
        )

        recommendations = sorted(
            analysis.recommendations,
            key=lambda recommendation: recommendation.property.name.casefold(),
        )

        for recommendation in recommendations:
            action = "include" if recommendation.include else "exclude"

            lines.extend(
                [
                    recommendation.property.name,
                    f"    Action     : {action}",
                    f"    Confidence : {int(recommendation.confidence)}%",
                    f"    Reason     : {recommendation.reason.title}",
                ]
            )

        output_view = self.query_one(
            "#snapshot-view",
            VerticalScroll,
        )

        content = self.query_one(
            "#snapshot-content",
            Static,
        )

        content.update("\n".join(lines))

        output_view.display = True
        output_view.scroll_home(animate=False)
        output_view.focus()
        self.update_instruction("Press Esc to return.")

    def action_help(self) -> None:
        """Show Help unless an operation is in progress."""

        if self.operation_in_progress:
            return

        self.show_help()

    def show_help(self) -> None:
        """Display the packaged help text."""

        workspace_ids = [
            "command-list",
            "capture-form",
            "device-selector",
            "profile-selector",
            "snapshot-view",
            "compare-view",
        ]

        self.help_previous_workspace = []

        for widget_id in workspace_ids:
            widget = self.query_one(
                f"#{widget_id}",
            )

            if widget.display:
                self.help_previous_workspace.append(widget_id)

            widget.display = False

        focused_widget = self.focused

        if focused_widget is not None:
            self.help_previous_focus = focused_widget.id
        else:
            self.help_previous_focus = None

        command_title = self.query_one(
            "#command-title",
            Static,
        )

        instruction = self.query_one(
            "#instruction",
            Static,
        )

        self.help_previous_title = str(command_title.render())
        self.help_previous_instruction = str(instruction.render())

        try:
            help_text = (
                files("configuration_engine").joinpath("help.txt").read_text(encoding="utf-8")
            )
        except OSError as exc:
            help_text = f"Unable to load help: {exc}"

        command_title.display = True
        self.update_command_title("Help")

        instruction.update("Press Esc to return.")

        help_view = self.query_one(
            "#help-view",
            VerticalScroll,
        )

        self.query_one(
            "#help-content",
            Static,
        ).update(help_text)

        help_view.display = True
        help_view.scroll_home(animate=False)
        help_view.focus()

    async def start_analyze(self) -> None:
        """Start the Analyze command workflow."""

        self.active_command = Command.DEVICE_ANALYZE
        self.snapshot_device = None

        self.query_one(
            "#command-device_analyze",
            ListItem,
        ).add_class("active-command")

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#capture-form").display = False

        self.query_one("#device-selector").display = True

        self.query_one("#profile-selector").display = False

        self.query_one("#snapshot-view").display = False

        self.query_one("#compare-view").display = False

        self.update_command_title(self.active_command.name)

        self.update_instruction("Select the device, then press Enter.")

        await self._show_device_selector()

    async def start_compare(self) -> None:
        """Start the Compare command workflow."""

        self.active_command = Command.DEVICE_COMPARE

        self.query_one(
            "#command-device_compare",
            ListItem,
        ).add_class("active-command")

        self.compare_device = None
        self.compare_profile = None

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#capture-form").display = False

        self.query_one("#device-selector").display = True

        self.query_one("#profile-selector").display = False

        self.query_one("#snapshot-view").display = False

        self.query_one("#compare-view").display = False

        self.update_command_title(
            self.active_command.name,
            self.compare_device,
            self.compare_profile,
        )

        self.update_instruction("Select the device, then press Enter.")

        await self._show_device_selector()

    async def start_apply(self) -> None:
        """Start the Apply command workflow."""

        self.active_command = Command.DEVICE_APPLY

        self.query_one(
            "#command-device_apply",
            ListItem,
        ).add_class("active-command")

        self.apply_device = None
        self.apply_profile = None

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one("#command-title").display = True

        self.query_one("#capture-form").display = False

        self.query_one("#device-selector").display = True

        self.query_one("#profile-selector").display = False

        self.query_one("#snapshot-view").display = False

        self.query_one("#compare-view").display = False

        self.update_command_title(
            self.active_command.name,
            self.apply_device,
            self.apply_profile,
        )

        self.update_instruction("Select the device, then press Enter.")

        await self._show_device_selector()

    async def show_compare_profiles(
        self,
    ) -> None:
        """Show the available profiles for comparison."""

        await self._show_profile_selector()

    async def show_compare(self) -> None:
        """Compare the selected device with the selected profile."""

        if self.compare_device is None:
            return

        if self.compare_profile is None:
            return

        engine = ConfigurationEngine.from_file(self.configuration_path())
        repository = self.profile_repository()

        self.operation_in_progress = True

        try:
            profile = repository.read(self.compare_profile)

            self.update_instruction("Please wait...")
            await asyncio.sleep(0)

            difference = await asyncio.to_thread(
                engine.compare,
                self.compare_device,
                profile,
            )

            self.mark_device_success(self.compare_device)

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.mark_device_unavailable(self.compare_device)
            self.show_operation_failure(f"Compare failed: {exc}")
            return

        finally:
            self.operation_in_progress = False

        table = self.query_one(
            "#compare-view",
            DataTable,
        )

        table.clear(columns=True)

        table.add_column(
            "Property",
            width=32,
        )

        table.add_column(
            "Current",
            width=30,
        )

        table.add_column(
            "Profile",
            width=30,
        )

        if difference.is_empty:
            table.add_row(
                "Device matches profile.",
                "",
                "",
            )
        else:
            for item in difference.differences:
                table.add_row(
                    item.property_name,
                    str(item.current_value),
                    str(item.desired_value),
                )

        table.display = True
        table.focus()

        self.update_instruction("Press Esc to return.")

    async def show_apply_profiles(
        self,
    ) -> None:
        """Show the available profiles for application."""

        await self._show_profile_selector()

    async def show_apply(self) -> None:
        """Apply the selected profile to the selected device."""

        if self.apply_device is None:
            return

        if self.apply_profile is None:
            return

        apply_device = self.apply_device

        self.update_instruction(
            "Please wait... Note that Esc is ignored until the command completes.",
        )

        await asyncio.sleep(0)

        self.operation_in_progress = True

        try:
            engine = ConfigurationEngine.from_file(self.configuration_path())

            repository = self.profile_repository()

            profile = repository.read(self.apply_profile)

            def update_apply_progress(message: str) -> None:
                self.call_from_thread(
                    self.update_instruction,
                    message,
                )

            def run_apply() -> ProfileDifference:
                return engine.apply(
                    apply_device,
                    profile,
                    on_progress=update_apply_progress,
                )

            difference = await asyncio.to_thread(
                run_apply,
            )

            self.mark_device_success(apply_device)

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.mark_device_unavailable(apply_device)
            self.show_operation_failure(f"Apply failed: {exc}")
            return

        finally:
            self.operation_in_progress = False

        if difference.is_empty:
            self.update_instruction(
                "No changes were required.\nPress Esc to return.",
            )
            return

        if difference.differences:
            self.update_instruction(
                "Apply completed successfully.\nPress Esc to return.",
            )

    def _load_devices_from_configuration(self) -> list[DeviceSummary]:
        """Load devices from the current configuration."""

        engine = ConfigurationEngine.from_file(
            self.configuration_path(),
        )

        return list(engine.devices())

    async def refresh_devices(self) -> None:
        """Refresh and alphabetize the device list."""

        device_list = self.query_one(
            "#device-list",
            ListView,
        )

        if not device_list.has_focus:
            return

        try:
            devices = sorted(
                self._load_devices_from_configuration(),
                key=lambda device: device.friendly_name.casefold(),
            )

        except (
            ValueError,
            OSError,
            TimeoutError,
        ) as exc:
            self.update_instruction(f"Refresh failed: {exc}")
            return

        selected_name: str | None = None

        if device_list.index is not None:
            index = device_list.index

            if 0 <= index < len(self.devices):
                selected_name = self.devices[index].friendly_name

        await device_list.clear()

        self.devices = devices

        for number, device in enumerate(
            self.devices,
            start=1,
        ):
            await device_list.append(
                self.make_device_list_item(
                    number,
                    device,
                )
            )

        if not self.devices:
            device_list.index = None
            self.update_instruction("No devices found.")
            return

        new_index = 0

        if selected_name is not None:
            for index, device in enumerate(
                self.devices,
            ):
                if device.friendly_name == selected_name:
                    new_index = index
                    break

        device_list.index = new_index
        device_list.focus()

        self.update_instruction(
            f"{len(self.devices)} devices found.",
        )

    async def on_mount(self) -> None:
        """Initialize the application after startup setup."""

        self.query_one("#command-title").display = False

        configuration_path = configuration_file(self.configuration_directory)

        if not configuration_path.is_file():
            self.hide_navigation_chrome()

            self.push_screen(
                FirstRunScreen(),
                self._first_run_complete,
            )
            return

        self.hide_navigation_chrome()

        self.push_screen(
            StartupScreen(),
            self._startup_complete,
        )

    def load_devices(self) -> None:
        """Load and display the available devices."""

        try:
            devices = self._load_devices_from_configuration()

            self.devices = sorted(
                devices,
                key=lambda device: (device.friendly_name or device.ieee_address).lower(),
            )

        except (
            OSError,
            ValueError,
            TimeoutError,
        ) as exc:
            self.devices = []

            self.update_instruction(
                f"Unable to load devices: {exc}",
            )

            return

        device_list = self.query_one(
            "#device-list",
            ListView,
        )

        device_list.clear()

        for index, device in enumerate(
            self.devices,
            start=1,
        ):
            name = device.friendly_name or device.ieee_address

            device_list.append(ListItem(Label(f"{index:>2}  {name}")))

        if self.devices:
            device_list.index = 0
            device_list.focus()

        command_list = self.query_one(
            "#command-list",
            ListView,
        )

        command_list.display = True
        command_list.clear()

        for command in Command:
            command_name = command.name.replace("_", " ").lower()
            command_id = command.name.lower()

            command_list.append(
                ListItem(
                    Label(command_name),
                    id=f"command-{command_id}",
                )
            )

        command_list.index = Command.PROFILE_LIST

        self.update_instruction(
            "Choose a command.",
        )

    def _first_run_complete(
        self,
        configuration_directory: Path | None,
    ) -> None:
        """Handle completion of first-run setup."""

        if configuration_directory is None:
            self.show_navigation_chrome()
            self.exit()
            return

        self.configuration_directory = configuration_directory

        self.push_screen(
            StartupScreen(),
            self._startup_complete,
        )

    def _startup_complete(
        self,
        result: object,
    ) -> None:
        """Finish startup and load the main application."""

        self.show_navigation_chrome()

        if result == "help":
            self.help_returns_to_startup = True
            self.show_help()
            return

        self.load_devices()

    def _settings_complete(
        self,
        configuration_directory: Path | None,
    ) -> None:
        """Finish the Settings workflow."""

        self.show_navigation_chrome()

        command_list = self.query_one(
            "#command-list",
            ListView,
        )

        command_list.display = True

        self.query_one(
            "#command-title",
        ).display = False

        self.query_one(
            "#command-program_setup",
            ListItem,
        ).remove_class("active-command")

        self.active_command = None

        if configuration_directory is None:
            command_list.index = Command.PROGRAM_SETUP
            command_list.focus()
            self.update_instruction(
                "Select a device, then choose a command.",
            )
            return

        self.configuration_directory = configuration_directory

        command_list.index = Command.PROGRAM_SETUP
        command_list.focus()

        self.update_instruction(
            "Select a device, then choose a command.",
        )

    def show_settings(self) -> None:
        """Display the Settings screen."""

        self.active_command = Command.PROGRAM_SETUP

        self.query_one(
            "#command-program_setup",
            ListItem,
        ).add_class("active-command")

        self.query_one(
            "#command-list",
            ListView,
        ).display = False

        self.query_one(
            "#command-title",
        ).display = True

        self.update_command_title(self.active_command.name)

        self.hide_navigation_chrome()

        self.push_screen(
            SettingsScreen(
                self.configuration_directory,
            ),
            self._settings_complete,
        )

    def _handle_device_selection(
        self,
        device: DeviceSummary,
    ) -> bool:
        """Handle selection of a device for the active command."""

        device_name = device.friendly_name

        if self.active_command == Command.DEVICE_SNAPSHOT:
            self.snapshot_device = device_name

            self.query_one(
                "#device-selector",
                Vertical,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.snapshot_device,
            )

            self.update_instruction(
                "Press Enter to capture the snapshot.",
            )

            return True

        if self.active_command == Command.DEVICE_INFO:
            self.snapshot_device = device_name

            self.query_one(
                "#device-selector",
                Vertical,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.snapshot_device,
            )

            self.update_instruction(
                "Press Enter to display device information.",
            )

            return True

        if self.active_command == Command.DEVICE_ANALYZE:
            self.snapshot_device = device_name

            self.query_one(
                "#device-selector",
                Vertical,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.snapshot_device,
            )

            self.update_instruction(
                "Press Enter to display analysis.",
            )

            return True

        if self.active_command == Command.DEVICE_COMPARE:
            self.compare_device = device_name

            self.query_one(
                "#capture-device-list",
                ListView,
            ).display = False

            self.update_instruction(
                "Select the profile, then press Enter.",
            )

            self.call_after_refresh(
                self.show_compare_profiles,
            )

            return True

        if self.active_command == Command.DEVICE_APPLY:
            self.apply_device = device_name

            self.query_one(
                "#capture-device-list",
                ListView,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.apply_device,
            )

            self.update_instruction(
                "Select the profile, then press Enter.",
            )

            self.call_after_refresh(
                self.show_apply_profiles,
            )

            return True

        return False

    def _handle_profile_selection(
        self,
        profile_name: str,
    ) -> bool:
        """Handle selection of a profile for the active command."""

        if self.active_command == Command.PROFILES_COMPARE:
            if self.profile_compare_first is None:
                self.profile_compare_first = profile_name

                self.update_command_title(
                    self.active_command.name,
                    self.profile_compare_first,
                )

                self.update_instruction(
                    "Select the second profile, then press Enter.",
                )

                return True

            self.profile_compare_second = profile_name

            self.query_one(
                "#profile-selector",
                Vertical,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.profile_compare_first,
                self.profile_compare_second,
            )

            self.update_instruction(
                "Press Enter to compare.",
            )

            return True

        if self.active_command == Command.DEVICE_COMPARE:
            self.compare_profile = profile_name

            self.query_one(
                "#profile-selector",
                Vertical,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.compare_device,
                self.compare_profile,
            )

            self.update_instruction(
                "Press Enter to compare.",
            )

            return True

        if self.active_command == Command.DEVICE_APPLY:
            self.apply_profile = profile_name

            self.query_one(
                "#profile-selector",
                Vertical,
            ).display = False

            self.update_command_title(
                self.active_command.name,
                self.apply_device,
                self.apply_profile,
            )

            self.update_instruction(
                "Press Enter to apply.",
            )

            return True

        return False

    def _return_to_command_list(
        self,
        command_list: ListView,
        command: Command,
        command_id: str,
    ) -> None:
        """Return from a command view to the command list."""

        command_list.display = True
        command_list.index = command

        self.query_one(
            "#command-title",
            Static,
        ).display = False

        self.query_one(
            command_id,
            ListItem,
        ).remove_class("active-command")

        command_list.focus()

        self.active_command = None

        self.update_command_title()
        self.update_instruction("Choose a command.")

    async def _start_selected_command(
        self,
        command: Command,
    ) -> None:
        """Start the selected command."""

        match command:
            case Command.PROFILE_LIST:
                await self.start_profile_list()
            case Command.PROFILES_COMPARE:
                await self.start_profiles_compare()
            case Command.DEVICE_INFO:
                await self.start_info()
            case Command.DEVICE_SNAPSHOT:
                await self.start_snapshot()
            case Command.DEVICE_ANALYZE:
                await self.start_analyze()
            case Command.DEVICE_CAPTURE:
                self.start_capture()
            case Command.DEVICE_COMPARE:
                await self.start_compare()
            case Command.DEVICE_APPLY:
                await self.start_apply()
            case Command.PROGRAM_SETUP:
                self.show_settings()

    async def on_list_view_selected(
        self,
        event: ListView.Selected,
    ) -> None:
        """Handle list selections."""

        if event.list_view.id == "command-list":
            index = event.list_view.index

            if index is None:
                return

            command = Command(index)

            await self._start_selected_command(command)

            return

        if event.list_view.id == "capture-device-list":
            index = event.list_view.index

            if index is None:
                return

            if index >= len(self.devices):
                return

            device = self.devices[index]

            if self._handle_device_selection(device):
                return

            self.capture_device = device.friendly_name

            self.query_one(
                "#capture-device-value",
                Static,
            ).update(device.friendly_name)

            self.query_one("#device-selector").display = False

            self.query_one("#capture-form").display = True

            self.capture_step = CaptureStep.READY

            self.update_capture_instruction()

            return

        if event.list_view.id == "compare-profile-list":
            index = event.list_view.index

            if index is None:
                return

            repository = self.profile_repository()
            profiles = repository.list()

            if index >= len(profiles):
                return

            profile_name = profiles[index]

            self._handle_profile_selection(profile_name)

            return

        if event.list_view.id == "profile-list-view":
            index = event.list_view.index

            if index is None:
                return

            repository = self.profile_repository()
            profiles = repository.list()

            if index >= len(profiles):
                return

            self.profile_list_profile = profiles[index]
            self.show_profile()

    async def on_key(
        self,
        event: events.Key,
    ) -> None:
        """Handle keyboard input for command selection and command actions."""

        if event.key == "question mark":
            event.prevent_default()
            self.action_help()
            return

        if event.key in {"r", "R"}:
            await self.refresh_devices()
            event.prevent_default()
            return

        if (
            event.key in {"n", "N"}
            and self.active_command == Command.PROFILE_LIST
            and self.query_one("#profile-view").display
            and self.profile_list_profile is not None
        ):
            rename_input = self.query_one(
                "#profile-rename-input",
                Input,
            )

            rename_input.value = self.profile_list_profile
            rename_input.display = True
            self.profile_rename_active = True
            self.profile_delete_active = False
            rename_input.focus()

            self.update_instruction(
                "Enter: Save   Esc: Cancel",
            )

            event.prevent_default()
            return

        if (
            event.key in {"d", "D"}
            and self.active_command == Command.PROFILE_LIST
            and self.query_one("#profile-view").display
            and self.profile_list_profile is not None
        ):
            self.profile_rename_active = False
            self.profile_delete_active = True

            content = self.query_one(
                "#profile-content",
                Static,
            )

            content.update(
                f"Delete profile?\n\n{self.profile_list_profile}\n\nEnter: Delete   Esc: Cancel"
            )

            self.update_instruction(
                "Enter: Delete   Esc: Cancel",
            )

            event.prevent_default()
            return

        if self.profile_delete_active:
            if event.key == "escape":
                self.profile_delete_active = False
                self.show_profile()

                event.prevent_default()
                return

            if event.key != "enter":
                return

            if self.profile_list_profile is None:
                return

            profile_name = self.profile_list_profile
            repository = self.profile_repository()

            try:
                repository.delete(
                    profile_name,
                )
            except (
                FileNotFoundError,
                OSError,
            ) as exc:
                self.profile_delete_active = False
                self.show_profile()

                self.update_instruction(
                    f"Delete failed: {exc}",
                )

                event.prevent_default()
                return

            self.profile_delete_active = False
            self.profile_list_profile = None

            if not await self._populate_profile_list():
                self.query_one(
                    "#profile-list",
                ).display = True
                self.query_one(
                    "#profile-view",
                ).display = False

                event.prevent_default()
                return

            self.query_one(
                "#profile-list",
            ).display = True
            self.query_one(
                "#profile-view",
            ).display = False

            self.update_instruction(
                "Select a profile, then press Enter.",
            )

            event.prevent_default()
            return

        if self.profile_rename_active:
            rename_input = self.query_one(
                "#profile-rename-input",
                Input,
            )

            if event.key == "escape":
                rename_input.display = False
                rename_input.value = ""
                self.profile_rename_active = False

                self.query_one(
                    "#profile-list-view",
                    ListView,
                ).focus()

                self.update_instruction(
                    "N: Rename   D: Delete   Esc: Back",
                )

                event.prevent_default()
                return

            if event.key != "enter":
                return

            new_name = rename_input.value.strip()

            if self.profile_list_profile is None:
                return

            if not new_name:
                self.update_instruction(
                    "Profile name cannot be empty. Enter a new name or press Esc.",
                )
                event.prevent_default()
                return

            repository = self.profile_repository()

            try:
                repository.rename(
                    self.profile_list_profile,
                    new_name,
                )
            except (
                FileExistsError,
                FileNotFoundError,
                OSError,
            ) as exc:
                self.update_instruction(
                    f"Rename failed: {exc}  Enter a new name or press Esc.",
                )
                event.prevent_default()
                return

            self.profile_list_profile = new_name

            rename_input.display = False
            rename_input.value = ""
            self.profile_rename_active = False

            await self._populate_profile_list()

            profile_list = self.query_one(
                "#profile-list-view",
                ListView,
            )

            profiles = repository.list()

            if new_name in profiles:
                profile_list.index = profiles.index(new_name)

            self.show_profile()

            event.prevent_default()
            return

        if event.key != "enter":
            return

        command_list = self.query_one(
            "#command-list",
            ListView,
        )

        if command_list.display and command_list.has_focus:
            index = command_list.index

            if index is None:
                return

            await self._start_selected_command(
                Command(index),
            )
            event.prevent_default()
            return

        match self.active_command:
            case Command.PROFILE_LIST:
                if self.profile_list_profile is None:
                    return

                event.prevent_default()
                self.show_profile()
                return
            case Command.PROFILES_COMPARE:
                if self.profile_compare_full_closed:
                    event.prevent_default()
                    self.show_profile_differences()
                    return

                if self.profile_compare_first is None:
                    return

                if self.profile_compare_second is None:
                    return

                event.prevent_default()
                self.show_profiles_compare()
                return
            case Command.DEVICE_INFO:
                if self.snapshot_device is None:
                    return

                event.prevent_default()
                await self.show_info()
                return
            case Command.DEVICE_SNAPSHOT:
                if self.snapshot_device is None:
                    return

                event.prevent_default()
                await self.show_snapshot()
                return
            case Command.DEVICE_ANALYZE:
                if self.snapshot_device is None:
                    return

                event.prevent_default()
                await self.show_analyze()
                return
            case Command.DEVICE_COMPARE:
                if self.compare_profile is None:
                    return

                event.prevent_default()
                await self.show_compare()
                return
            case Command.DEVICE_APPLY:
                if self.apply_device is None:
                    return

                if self.apply_profile is None:
                    return

                event.prevent_default()
                await self.show_apply()
                return

        if self.active_command != Command.DEVICE_CAPTURE:
            return

        if self.capture_step != CaptureStep.READY:
            return

        if self.capture_device is None:
            return

        event.prevent_default()
        await self.capture_profile()

    async def action_back(self) -> None:
        """Return to the previous interface level."""

        if self.operation_in_progress:
            return

        help_view = self.query_one(
            "#help-view",
            VerticalScroll,
        )

        if help_view.display:
            help_view.display = False

            if self.help_returns_to_startup:
                self.help_returns_to_startup = False

                self.query_one(
                    "#command-title",
                    Static,
                ).display = False

                self.push_screen(
                    StartupScreen(),
                    self._startup_complete,
                )

                return

            for widget_id in self.help_previous_workspace:
                self.query_one(
                    f"#{widget_id}",
                ).display = True

            command_title = self.query_one(
                "#command-title",
                Static,
            )

            instruction = self.query_one(
                "#instruction",
                Static,
            )

            if self.help_previous_title is not None:
                command_title.update(
                    self.help_previous_title,
                )

            if self.help_previous_instruction is not None:
                instruction.update(
                    self.help_previous_instruction,
                )

            if self.help_previous_focus is not None:
                previous_focus = self.query_one(
                    f"#{self.help_previous_focus}",
                )
                previous_focus.focus()

            self.help_previous_workspace = []
            self.help_previous_focus = None
            self.help_previous_title = None
            self.help_previous_instruction = None

            return

        capture_form = self.query_one("#capture-form")
        selector = self.query_one("#device-selector")
        profile_selector = self.query_one("#profile-selector")
        snapshot_view = self.query_one("#snapshot-view")
        compare_view = self.query_one("#compare-view")

        command_list = self.query_one(
            "#command-list",
            ListView,
        )

        command_title = self.query_one(
            "#command-title",
            Static,
        )

        if self.operation_failed:
            self.operation_failed = False

            command_list.display = True
            command_list.focus()

            if self.active_command is not None:
                command_list.index = self.active_command

                command_id = f"#command-{self.active_command}"
                self.query_one(
                    command_id,
                    ListItem,
                ).remove_class("active-command")

            self.query_one("#command-title").display = False

            self.snapshot_device = None
            self.compare_device = None
            self.compare_profile = None
            self.apply_device = None
            self.apply_profile = None
            self.active_command = None

            self.update_command_title()
            self.update_instruction("Choose a command.")

            return

        # ------------------------------------------------------------
        # Analyze device selection -> command list
        # ------------------------------------------------------------

        if (
            self.active_command == Command.DEVICE_ANALYZE
            and self.snapshot_device is not None
            and not snapshot_view.display
            and not selector.display
        ):
            self._return_to_command_list(
                command_list,
                Command.DEVICE_ANALYZE,
                "#command-device_analyze",
            )

            self.snapshot_device = None

            return

        # ------------------------------------------------------------
        # Info result -> command list
        # ------------------------------------------------------------

        if snapshot_view.display and self.active_command == Command.DEVICE_INFO:
            snapshot_view.display = False
            selector.display = False
            command_title.display = False

            command_list.display = True
            command_list.index = self.active_command

            self.query_one(
                "#command-device_info",
                ListItem,
            ).remove_class("active-command")

            command_list.focus()

            self.snapshot_device = None
            self.active_command = None

            self.update_command_title()
            self.update_instruction("Choose a command.")

            return

        # ------------------------------------------------------------
        # Analyze result -> command list
        # ------------------------------------------------------------

        if snapshot_view.display and self.active_command == Command.DEVICE_ANALYZE:
            snapshot_view.display = False
            selector.display = False
            command_title.display = False

            command_list.display = True
            command_list.index = self.active_command

            self.query_one(
                "#command-device_analyze",
                ListItem,
            ).remove_class("active-command")

            command_list.focus()

            self.snapshot_device = None
            self.active_command = None

            self.update_command_title()
            self.update_instruction("Choose a command.")

            return

        # ------------------------------------------------------------
        # Profiles Compare initial selection -> command list
        # ------------------------------------------------------------

        if (
            self.active_command == Command.PROFILES_COMPARE
            and self.profile_compare_first is None
            and self.profile_compare_second is None
        ):
            profile_selector.display = False

            self._return_to_command_list(
                command_list,
                Command.PROFILES_COMPARE,
                "#command-profiles_compare",
            )

            self.profile_compare_show_differences = False
            self.profile_compare_full_closed = False

            return

        # ------------------------------------------------------------
        # Profiles Compare -> command list
        # ------------------------------------------------------------

        if (
            self.active_command == Command.PROFILES_COMPARE
            and self.profile_compare_first is not None
            and self.profile_compare_second is None
        ):
            profile_selector.display = False

            self._return_to_command_list(
                command_list,
                Command.PROFILES_COMPARE,
                "#command-profiles_compare",
            )

            self.profile_compare_first = None
            self.profile_compare_second = None
            self.profile_compare_show_differences = False
            self.profile_compare_full_closed = False

            return

        # ------------------------------------------------------------
        # Profiles Compare -> command list before comparison
        # ------------------------------------------------------------

        if (
            self.active_command == Command.PROFILES_COMPARE
            and self.profile_compare_first is not None
            and self.profile_compare_second is not None
            and not compare_view.display
            and not self.profile_compare_show_differences
            and not self.profile_compare_full_closed
        ):
            self._return_to_command_list(
                command_list,
                Command.PROFILES_COMPARE,
                "#command-profiles_compare",
            )

            self.profile_compare_first = None
            self.profile_compare_second = None
            self.profile_compare_show_differences = False
            self.profile_compare_full_closed = False

            return

        # ------------------------------------------------------------
        # Profiles comparison -> difference prompt
        # ------------------------------------------------------------

        if (
            compare_view.display
            and self.active_command == Command.PROFILES_COMPARE
            and not self.profile_compare_show_differences
        ):
            compare_view.display = False

            self.profile_compare_full_closed = True

            self.update_instruction(
                "Press Enter to show differences. Press Esc to exit Profiles Compare.",
            )

            return

        # ------------------------------------------------------------
        # Profile detail -> profile list
        # ------------------------------------------------------------

        if self.query_one("#profile-view").display:
            self.query_one("#profile-view").display = False
            self.query_one("#profile-list").display = True

            profile_list = self.query_one(
                "#profile-list-view",
                ListView,
            )

            profile_list.focus()

            self.update_instruction(
                "Select a profile, then press Enter.",
            )

            return

        # ------------------------------------------------------------
        # Profiles differences -> command list
        # ------------------------------------------------------------

        if (
            compare_view.display
            and self.active_command == Command.PROFILES_COMPARE
            and self.profile_compare_show_differences
        ):
            compare_view.display = False

            self._return_to_command_list(
                command_list,
                Command.PROFILES_COMPARE,
                "#command-profiles_compare",
            )

            self.profile_compare_first = None
            self.profile_compare_second = None
            self.profile_compare_show_differences = False
            self.profile_compare_full_closed = False

            return

        # ------------------------------------------------------------
        # Profile list -> command list
        # ------------------------------------------------------------

        if self.query_one("#profile-list").display:
            self.query_one("#profile-list").display = False

            self._return_to_command_list(
                command_list,
                Command.PROFILE_LIST,
                "#command-profile_list",
            )

            self.profile_list_profile = None

            return

        # ------------------------------------------------------------
        # Snapshot result -> command list
        # ------------------------------------------------------------

        if snapshot_view.display:
            snapshot_view.display = False
            selector.display = False

            self._return_to_command_list(
                command_list,
                Command.DEVICE_SNAPSHOT,
                "#command-device_snapshot",
            )

            self.snapshot_device = None

            return

        # ------------------------------------------------------------
        # Device Compare device selection -> command list
        # ------------------------------------------------------------

        if (
            self.active_command == Command.DEVICE_COMPARE
            and self.compare_device is not None
            and self.compare_profile is None
            and not compare_view.display
        ):
            profile_selector.display = False

            self._return_to_command_list(
                command_list,
                Command.DEVICE_COMPARE,
                "#command-device_compare",
            )

            self.compare_device = None
            self.compare_profile = None

            return

        # ------------------------------------------------------------
        # Device Compare selection -> command list before comparison
        # ------------------------------------------------------------

        if (
            self.active_command == Command.DEVICE_COMPARE
            and self.compare_device is not None
            and self.compare_profile is not None
            and not compare_view.display
        ):
            self._return_to_command_list(
                command_list,
                Command.DEVICE_COMPARE,
                "#command-device_compare",
            )

            self.compare_device = None
            self.compare_profile = None

            return

        # ------------------------------------------------------------
        # Compare result -> command list
        # ------------------------------------------------------------

        if compare_view.display and self.active_command == Command.DEVICE_COMPARE:
            compare_view.display = False

            self._return_to_command_list(
                command_list,
                self.active_command,
                "#command-device_compare",
            )

            self.compare_device = None
            self.compare_profile = None

            return

        # ------------------------------------------------------------
        # Device Apply selection -> command list before apply
        # ------------------------------------------------------------

        if (
            self.active_command == Command.DEVICE_APPLY
            and self.apply_device is not None
            and self.apply_profile is not None
            and not compare_view.display
            and not profile_selector.display
            and not selector.display
        ):
            self._return_to_command_list(
                command_list,
                Command.DEVICE_APPLY,
                "#command-device_apply",
            )

            self.apply_device = None
            self.apply_profile = None

            return

        # ------------------------------------------------------------
        # Apply result -> command list
        # ------------------------------------------------------------

        if compare_view.display and self.active_command == Command.DEVICE_APPLY:
            compare_view.display = False

            self._return_to_command_list(
                command_list,
                self.active_command,
                "#command-device_apply",
            )

            self.apply_device = None
            self.apply_profile = None

            return

        # ------------------------------------------------------------
        # Profile selector -> device selector
        # ------------------------------------------------------------

        if profile_selector.display:
            profile_selector.display = False

            selector.display = True
            selector.focus()

            if self.active_command == Command.DEVICE_APPLY:
                self.apply_profile = None
            else:
                self.compare_profile = None

            self.update_instruction("Select the device, then press Enter.")

            return

        # ------------------------------------------------------------
        # Device selector / Capture form -> command list
        # ------------------------------------------------------------

        if capture_form.display or selector.display:
            capture_form.display = False
            selector.display = False

            command_title.display = False
            command_list.display = True

            match self.active_command:
                case Command.DEVICE_INFO:
                    command_list.index = self.active_command

                    self.query_one(
                        "#command-device_info",
                        ListItem,
                    ).remove_class("active-command")
                case Command.DEVICE_SNAPSHOT:
                    command_list.index = self.active_command

                    self.query_one(
                        "#command-device_snapshot",
                        ListItem,
                    ).remove_class("active-command")
                case Command.DEVICE_ANALYZE:
                    command_list.index = self.active_command

                    self.query_one(
                        "#command-device_analyze",
                        ListItem,
                    ).remove_class("active-command")
                case Command.DEVICE_CAPTURE:
                    command_list.index = self.active_command

                    self.query_one(
                        "#command-device_capture",
                        ListItem,
                    ).remove_class("active-command")
                case Command.DEVICE_COMPARE:
                    command_list.index = self.active_command

                    self.query_one(
                        "#command-device_compare",
                        ListItem,
                    ).remove_class("active-command")
                case Command.DEVICE_APPLY:
                    command_list.index = self.active_command

                    self.query_one(
                        "#command-device_apply",
                        ListItem,
                    ).remove_class("active-command")

            command_list.focus()

            self.capture_step = CaptureStep.PROFILE_NAME
            self.capture_profile_name = ""
            self.capture_device = None

            self.snapshot_device = None

            self.compare_device = None
            self.compare_profile = None

            self.apply_device = None
            self.apply_profile = None

            self.active_command = None

            self.update_command_title()
            self.update_instruction("Choose a command.")

            return

        # ------------------------------------------------------------
        # Nothing active -> exit application
        # ------------------------------------------------------------

        self.exit()

    async def on_input_submitted(
        self,
        event: Input.Submitted,
    ) -> None:
        """Advance the capture workflow when an input is submitted."""

        if event.input.id != "capture-profile":
            return

        if not event.value.strip():
            return

        self.capture_profile_name = event.value.strip()

        self.capture_step = CaptureStep.SOURCE_DEVICE

        self.update_capture_instruction()

        await self.show_capture_device_selector()


def main() -> None:
    """Run the Configuration Engine terminal application."""

    ConfigurationApp().run()


if __name__ == "__main__":
    main()
