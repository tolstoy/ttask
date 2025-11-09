"""Help screen widget showing keyboard shortcuts."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.binding import Binding


class HelpScreen(Screen):
    """Modal screen showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("h", "dismiss", "Close", show=False),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(26, 26, 46, 0.9);
    }

    #help_container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: #2d2d44;
        border: thick #0abdc6;
        padding: 1 2;
    }

    #help_title {
        text-align: center;
        text-style: bold;
        color: #0abdc6;
        margin-bottom: 1;
    }

    #help_content {
        height: auto;
        overflow-y: auto;
        color: #e2e8f0;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with VerticalScroll(id="help_container"):
            yield Static("Keyboard Shortcuts", id="help_title")
            yield Static(self.get_help_text(), id="help_content")

    def get_help_text(self) -> str:
        """Get formatted help text."""
        return """[bold]Navigation[/bold]
↑/↓ or j/k    Move selection up/down
←/→ or h/l    Previous/next day
Shift+←       Previous day with tasks (skip empty days)
Shift+→       Next day with tasks (skip empty days)
t             Jump to today

[bold]Task Operations[/bold]
a             Add new task
              • On child task: adds sibling below at same indent
              • On parent task: adds new parent at bottom
e             Edit selected task
Space or x    Toggle task completion
d             Delete selected task
Tab           Indent task (nest under previous)
Shift+Tab     Unindent task

[bold]Organization[/bold]
f             Toggle fold/unfold (collapse/expand children)
Shift+↑       Move task and children up (swaps with sibling)
Shift+↓       Move task and children down (swaps with sibling)

[bold]Advanced[/bold]
m             Move task to another day
              • Natural language: tomorrow, yesterday, monday
              • Relative: +1, -1, +7, next week, last week
              • Month + day: nov 10, december 25
              • ISO format: YYYY-MM-DD

[bold]General[/bold]
h             Show this help
q             Quit

[dim]Press Esc or H to close this help[/dim]"""

    def action_dismiss(self) -> None:
        """Close the help screen."""
        self.app.pop_screen()
