from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static


class StartupScreen(ModalScreen[str | None]):
    """Display the brief navigation reminder at application startup."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("enter", "continue", "Continue"),
        Binding("question_mark", "help", "Help"),
    ]

    DEFAULT_CSS = """
    StartupScreen {
        align: center middle;
    }

    #startup-box {
        width: 60;
        height: auto;
        padding: 2 4;
        border: round $accent;
        background: $surface;
    }

    #startup-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #startup-help {
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="startup-box"):
            yield Label(
                "Navigation",
                id="startup-title",
            )

            yield Static(
                "- Arrow keys\n- Tab / Shift-Tab to change window\n- Enter\n- Esc\n- ? for Help"
            )

            yield Static(
                "Press Enter to continue.",
                id="startup-help",
            )

    def action_continue(self) -> None:
        """Dismiss the startup screen."""

        self.dismiss(None)

    def action_help(self) -> None:
        """Request the help screen."""

        self.dismiss("help")
