"""Help screen widget showing keyboard shortcuts."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.binding import Binding
from textual import events


class HelpScreen(Screen):
    """Modal screen showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
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
g             Jump to today

[bold]Task Operations[/bold]
a             Add new task
              • On child task: adds sibling below at same indent
              • On parent task: adds new parent at bottom
r             Edit/rename selected task
Space or x    Toggle task completion (or selection in visual mode)
d             Delete selected task (or all selected in visual mode)
u             Undo last delete (keeps last 20 operations)
Tab           Indent task (nest under previous)
Shift+Tab     Unindent task

[bold]Time Tracking[/bold]
t             Toggle timer (start/stop) for selected task
              • Press once to START (shows [1:23/30m] live)
              • Press again to STOP (adds elapsed time to task)
              • Timer runs in background - works across tasks/days
              • Only adds time if ≥1 minute elapsed
Shift+T       Clear ALL time tracking from task
              • Removes estimate, actual time, and running timer
              • Use to completely reset time tracking
e             Set/edit time estimate for task
              • Formats: 30, 90s, 1h30m, 2.5m, 1h30m15s
              • Lower estimates = higher score multiplier!
+             Manually add time to task (e.g., +15)
-             Manually subtract time from task
Shift+S       Show detailed statistics screen
              • Daily score, streak, efficiency
              • Tasks beat vs. over estimate
              • Scoring formula explanation

[bold]Visual Selection Mode[/bold]
v             Enter/exit visual selection mode
Space or x    Toggle selection of task (and all children)
              • Selected tasks show ✓ marker
              • Selecting parent auto-selects children
d             Delete all selected tasks
m             Move all selected tasks to another day
              • Selection mode exits automatically on day change

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

[dim]Press Esc to close this help[/dim]"""

    def on_key(self, event: events.Key) -> None:
        """Handle key events - block all except Esc and arrow keys."""
        # Allow Esc (handled by binding) and arrow keys (for scrolling)
        if event.key not in ("escape", "up", "down"):
            event.prevent_default()
            event.stop()

    def action_dismiss(self) -> None:
        """Close the help screen."""
        self.dismiss()
