"""Main TUI application for task journal."""
from datetime import date, timedelta
from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Input
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.screen import Screen
from textual import events
from markdown_handler import MarkdownHandler
from models import DailyTaskList, Task


class TaskListWidget(Static):
    """Widget to display the list of tasks."""

    def __init__(self, daily_list: DailyTaskList):
        super().__init__()
        self.daily_list = daily_list
        self.selected_index = 0

    def has_children(self, index: int) -> bool:
        """Check if task at index has children (next task has higher indent)."""
        if index >= len(self.daily_list.tasks) - 1:
            return False
        current_indent = self.daily_list.tasks[index].indent_level
        next_indent = self.daily_list.tasks[index + 1].indent_level
        return next_indent > current_indent

    def is_task_visible(self, index: int) -> bool:
        """Check if task at index is visible (not hidden by a folded parent)."""
        if index < 0 or index >= len(self.daily_list.tasks):
            return False

        task_indent = self.daily_list.tasks[index].indent_level

        # Check all previous tasks to see if any folded parent hides this task
        for i in range(index - 1, -1, -1):
            prev_task = self.daily_list.tasks[i]
            # If we find a task with lower indent, it could be a parent
            if prev_task.indent_level < task_indent:
                # If this parent is folded, our task is hidden
                if prev_task.folded:
                    return False
                # Update our reference indent to continue checking higher parents
                task_indent = prev_task.indent_level
            # If we're back to indent 0 and it's not folded, we're visible
            if prev_task.indent_level == 0:
                break

        return True

    def render(self) -> str:
        """Render the task list."""
        if not self.daily_list.tasks:
            return "[dim]No tasks for today. Press 'a' to add one.[/dim]"

        lines = []
        skip_until_indent = None

        for i, task in enumerate(self.daily_list.tasks):
            # Skip children of folded tasks
            if skip_until_indent is not None:
                if task.indent_level > skip_until_indent:
                    continue
                else:
                    skip_until_indent = None

            # Selection marker
            marker = ">" if i == self.selected_index else " "

            # Add fold indicator - always use 2 chars for consistent alignment
            fold_indicator = "  "  # Default: two spaces
            if self.has_children(i):
                if task.folded:
                    fold_indicator = "▶ "
                    skip_until_indent = task.indent_level
                else:
                    fold_indicator = "▼ "

            # Create the task display
            indent = "  " * task.indent_level
            # Escape brackets so they're not interpreted as markup
            checkbox = "\\[x]" if task.completed else "\\[ ]"

            # Content with strikethrough if completed
            if task.completed:
                content = f"[strike]{task.content}[/strike]"
            else:
                content = task.content

            # Highlight selected item - fold indicator comes before indent
            if i == self.selected_index:
                line = f"[#ff006e on #2d2d44]{marker} [#0abdc6]{fold_indicator}[/#0abdc6]{indent}{checkbox} {content}[/#ff006e on #2d2d44]"
            else:
                line = f"{marker} [#0abdc6]{fold_indicator}[/#0abdc6]{indent}{checkbox} {content}"

            lines.append(line)

        return "\n".join(lines)

    def get_visible_line_number(self, task_index: int) -> int:
        """Get the visible line number for a task index (accounting for folded tasks)."""
        visible_line = 0
        skip_until_indent = None

        for i in range(len(self.daily_list.tasks)):
            task = self.daily_list.tasks[i]

            # Skip children of folded tasks
            if skip_until_indent is not None:
                if task.indent_level > skip_until_indent:
                    if i == task_index:
                        # This task is hidden, shouldn't happen but return 0
                        return 0
                    continue
                else:
                    skip_until_indent = None

            # Check if this task has children and is folded
            if self.has_children(i) and task.folded:
                skip_until_indent = task.indent_level

            # If this is our target task, return the current visible line
            if i == task_index:
                return visible_line

            visible_line += 1

        return visible_line

    def move_selection(self, delta: int):
        """Move the selection up or down, skipping hidden tasks."""
        if not self.daily_list.tasks:
            return

        # Start from current position
        new_index = self.selected_index

        # Keep moving in the direction until we find a visible task
        while True:
            new_index += delta

            # Check bounds
            if new_index < 0:
                new_index = 0
                break
            if new_index >= len(self.daily_list.tasks):
                new_index = len(self.daily_list.tasks) - 1
                break

            # If this task is visible, we found our target
            if self.is_task_visible(new_index):
                break

            # If we've wrapped around to where we started, stop
            if new_index == self.selected_index:
                return

        self.selected_index = new_index
        self.refresh()

        # Scroll to keep the selected task visible
        self.scroll_to_selected()

    def scroll_to_selected(self):
        """Scroll the parent container only when selected task reaches viewport edges."""
        if not self.daily_list.tasks:
            return

        # Get the visible line number of the selected task
        line_number = self.get_visible_line_number(self.selected_index)

        # Get the parent container
        try:
            container = self.parent
            if container and hasattr(container, 'scroll_offset') and hasattr(container, 'size'):
                # Get current scroll position and viewport height
                scroll_y = container.scroll_offset.y
                viewport_height = container.size.height

                # Calculate visible range
                visible_top = scroll_y
                visible_bottom = scroll_y + viewport_height - 1

                # Only scroll if the line is outside the visible range
                if line_number < visible_top:
                    # Selected task is above viewport, scroll up to show it
                    container.scroll_to(y=line_number, animate=False)
                elif line_number > visible_bottom:
                    # Selected task is below viewport, scroll down to show it at bottom
                    new_scroll_y = line_number - viewport_height + 1
                    container.scroll_to(y=max(0, new_scroll_y), animate=False)
                # Otherwise, task is already visible, don't scroll
        except Exception:
            # If scrolling fails for any reason, just continue
            pass

    def get_selected_task(self) -> Task | None:
        """Get the currently selected task."""
        if 0 <= self.selected_index < len(self.daily_list.tasks):
            return self.daily_list.tasks[self.selected_index]
        return None


class CenteredFooter(Static):
    """Custom footer with centered content."""

    def __init__(self):
        super().__init__()
        self.update("[dim]Press[/dim] [bold]H[/bold] [dim]for Help  •  [/dim][bold]Q[/bold] [dim]to Quit[/dim]")

    DEFAULT_CSS = """
    CenteredFooter {
        background: #0abdc6;
        color: #ffffff;
        dock: bottom;
        height: 1;
        text-align: center;
    }
    """


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
        with Container(id="help_container"):
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


class TaskJournalApp(App):
    """A terminal-based daily task journal."""

    TITLE = "tTask"

    CSS = """
    Screen {
        background: #1a1a2e;
    }

    Header {
        background: #2d2d44;
        color: #0abdc6;
    }

    #date_header {
        height: 3;
        content-align: center middle;
        background: #0abdc6;
        color: #ffffff;
        text-style: bold;
    }

    #task_list {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        background: #1a1a2e;
    }

    TaskListWidget {
        height: auto;
        color: #e2e8f0;
    }

    #input_container {
        height: auto;
        padding: 1;
        background: #1a1a2e;
    }

    Input {
        margin: 0 1;
        background: #2d2d44;
        color: #ffffff;
        border: tall #8b5cf6;
    }

    Input:focus {
        border: tall #0abdc6;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True, show=False),
        Binding("h", "show_help", "Help", show=False),
        Binding("a", "add_task", "Add", show=False),
        Binding("x", "toggle_complete", "Complete", show=False),
        Binding("space", "toggle_complete", "Complete", show=False),
        Binding("d", "delete_task", "Delete", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("up", "move_up", "Up", show=False),
        Binding("shift+up", "move_task_up", "S-↑ Move", show=False),
        Binding("shift+down", "move_task_down", "S-↓ Move", show=False),
        Binding("left", "prev_day", "Prev Day", show=False),
        Binding("right", "next_day", "Next Day", show=False),
        Binding("shift+left", "prev_non_empty_day", "S-← Skip", show=False),
        Binding("shift+right", "next_non_empty_day", "S-→ Skip", show=False),
        Binding("l", "next_day", "Next Day", show=False),
        Binding("t", "today", "Today", show=False),
        Binding("tab", "indent", "Indent", show=False),
        Binding("shift+tab", "unindent", "Unindent", show=False),
        Binding("f", "toggle_fold", "Fold", show=False),
        Binding("m", "move_task", "Move", show=False),
        Binding("e", "edit_task", "Edit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.handler = MarkdownHandler()
        self.current_date = date.today()
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.adding_task = False
        self.editing_task = False
        self.moving_task = False
        self.task_to_move = None
        self.new_task_insert_index = None
        self.new_task_indent_level = 0

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        yield Static(id="date_header")
        yield Container(
            TaskListWidget(self.daily_list),
            id="task_list"
        )
        yield Container(id="input_container")
        yield CenteredFooter()

    def on_mount(self) -> None:
        """Set up the app after mounting."""
        self.update_date_header()

    def update_date_header(self):
        """Update the date header."""
        header = self.query_one("#date_header", Static)
        date_str = self.current_date.strftime("%A, %B %d, %Y")
        header.update(date_str)

    def refresh_task_list(self):
        """Refresh the task list widget."""
        task_widget = self.query_one(TaskListWidget)
        task_widget.daily_list = self.daily_list
        # Ensure selected_index is valid
        if len(self.daily_list.tasks) == 0:
            task_widget.selected_index = 0
        else:
            task_widget.selected_index = min(task_widget.selected_index,
                                            len(self.daily_list.tasks) - 1)

            # If the selected task is now hidden (folded), find nearest visible task
            if not task_widget.is_task_visible(task_widget.selected_index):
                # Try going up first
                found = False
                for i in range(task_widget.selected_index - 1, -1, -1):
                    if task_widget.is_task_visible(i):
                        task_widget.selected_index = i
                        found = True
                        break

                # If not found going up, try going down
                if not found:
                    for i in range(task_widget.selected_index + 1, len(self.daily_list.tasks)):
                        if task_widget.is_task_visible(i):
                            task_widget.selected_index = i
                            found = True
                            break

                # If still not found, default to 0
                if not found:
                    task_widget.selected_index = 0

        # Force a complete refresh
        task_widget.refresh(layout=True)

        # Scroll to keep the selected task visible
        task_widget.scroll_to_selected()

    def save_current_tasks(self):
        """Save the current task list."""
        self.handler.save_tasks(self.daily_list)

    def action_move_down(self):
        """Move selection down."""
        task_widget = self.query_one(TaskListWidget)
        task_widget.move_selection(1)

    def action_move_up(self):
        """Move selection up."""
        task_widget = self.query_one(TaskListWidget)
        task_widget.move_selection(-1)

    def action_toggle_complete(self):
        """Toggle completion of selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if task:
            task.toggle_complete()
            self.save_current_tasks()
            self.refresh_task_list()

    def action_delete_task(self):
        """Delete the selected task."""
        task_widget = self.query_one(TaskListWidget)
        if self.daily_list.tasks:
            self.daily_list.remove_task(task_widget.selected_index)
            self.save_current_tasks()
            self.refresh_task_list()

    def action_indent(self):
        """Indent the selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if task and task.indent_level < 5:  # Max 5 levels
            task.indent_level += 1
            self.save_current_tasks()
            self.refresh_task_list()

    def action_unindent(self):
        """Unindent the selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if task and task.indent_level > 0:
            task.indent_level -= 1
            self.save_current_tasks()
            self.refresh_task_list()

    def action_toggle_fold(self):
        """Toggle fold status of selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if task and task_widget.has_children(task_widget.selected_index):
            task.toggle_fold()
            self.save_current_tasks()
            self.refresh_task_list()

    def get_task_group(self, start_index: int) -> tuple[int, int]:
        """Get the range of tasks that form a group (parent + children).
        Returns (start_index, end_index) inclusive.
        """
        if start_index >= len(self.daily_list.tasks):
            return (start_index, start_index)

        parent_indent = self.daily_list.tasks[start_index].indent_level
        end_index = start_index

        # Find all consecutive children with higher indent
        for i in range(start_index + 1, len(self.daily_list.tasks)):
            if self.daily_list.tasks[i].indent_level > parent_indent:
                end_index = i
            else:
                break

        return (start_index, end_index)

    def find_prev_sibling_group(self, index: int) -> tuple[int, int] | None:
        """Find the previous sibling group at the same indent level.
        Returns (start, end) of the sibling group, or None if not found.
        """
        current_task = self.daily_list.tasks[index]
        target_indent = current_task.indent_level

        # Search backwards for a task at the same indent level
        for i in range(index - 1, -1, -1):
            task = self.daily_list.tasks[i]
            if task.indent_level == target_indent:
                # Found a sibling! Get its group range
                return self.get_task_group(i)
            elif task.indent_level < target_indent:
                # Found a parent (lower indent), no more siblings above
                return None

        return None

    def find_next_sibling_group(self, index: int) -> tuple[int, int] | None:
        """Find the next sibling group at the same indent level.
        Returns (start, end) of the sibling group, or None if not found.
        """
        current_task = self.daily_list.tasks[index]
        target_indent = current_task.indent_level

        # First skip over the current task's children
        _, current_end = self.get_task_group(index)

        # Search forward from after current group
        for i in range(current_end + 1, len(self.daily_list.tasks)):
            task = self.daily_list.tasks[i]
            if task.indent_level == target_indent:
                # Found a sibling! Get its group range
                return self.get_task_group(i)
            elif task.indent_level < target_indent:
                # Found a task with lower indent (uncle/parent level), no more siblings
                return None

        return None

    def action_move_task_up(self):
        """Move selected task (and its children) up, only within same indent level."""
        task_widget = self.query_one(TaskListWidget)
        if task_widget.selected_index <= 0:
            return

        # Get current task group
        current_start, current_end = self.get_task_group(task_widget.selected_index)

        # Find previous sibling at the same indent level
        prev_group = self.find_prev_sibling_group(task_widget.selected_index)
        if prev_group is None:
            # No sibling above at same level, can't move
            return

        prev_start, prev_end = prev_group

        # Extract groups
        current_group = self.daily_list.tasks[current_start:current_end + 1]
        prev_group_tasks = self.daily_list.tasks[prev_start:prev_end + 1]

        # Rebuild task list with swapped groups
        new_tasks = (
            self.daily_list.tasks[:prev_start] +
            current_group +
            prev_group_tasks +
            self.daily_list.tasks[current_end + 1:]
        )

        self.daily_list.tasks = new_tasks
        task_widget.selected_index = prev_start
        self.save_current_tasks()
        self.refresh_task_list()

    def action_move_task_down(self):
        """Move selected task (and its children) down, only within same indent level."""
        task_widget = self.query_one(TaskListWidget)

        # Get current task group
        current_start, current_end = self.get_task_group(task_widget.selected_index)

        # Find next sibling at the same indent level
        next_group = self.find_next_sibling_group(task_widget.selected_index)
        if next_group is None:
            # No sibling below at same level, can't move
            return

        next_start, next_end = next_group

        # Extract groups
        current_group = self.daily_list.tasks[current_start:current_end + 1]
        next_group_tasks = self.daily_list.tasks[next_start:next_end + 1]

        # Rebuild task list with swapped groups
        new_tasks = (
            self.daily_list.tasks[:current_start] +
            next_group_tasks +
            current_group +
            self.daily_list.tasks[next_end + 1:]
        )

        self.daily_list.tasks = new_tasks
        task_widget.selected_index = current_start + len(next_group_tasks)
        self.save_current_tasks()
        self.refresh_task_list()

    def action_next_day(self):
        """Navigate to next day."""
        self.current_date += timedelta(days=1)
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.update_date_header()
        self.refresh_task_list()

    def action_prev_day(self):
        """Navigate to previous day."""
        self.current_date -= timedelta(days=1)
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.update_date_header()
        self.refresh_task_list()

    def find_prev_non_empty_day(self, start_date: date, max_days: int = 365) -> date | None:
        """Find the previous day that has incomplete tasks."""
        check_date = start_date - timedelta(days=1)
        for _ in range(max_days):
            file_path = self.handler.get_file_path(check_date)
            if file_path.exists():
                # Check if file has tasks with at least one incomplete
                daily_list = self.handler.load_tasks(check_date)
                if daily_list.tasks and any(not task.completed for task in daily_list.tasks):
                    return check_date
            check_date -= timedelta(days=1)
        return None

    def find_next_non_empty_day(self, start_date: date, max_days: int = 365) -> date | None:
        """Find the next day that has incomplete tasks."""
        check_date = start_date + timedelta(days=1)
        for _ in range(max_days):
            file_path = self.handler.get_file_path(check_date)
            if file_path.exists():
                # Check if file has tasks with at least one incomplete
                daily_list = self.handler.load_tasks(check_date)
                if daily_list.tasks and any(not task.completed for task in daily_list.tasks):
                    return check_date
            check_date += timedelta(days=1)
        return None

    def action_prev_non_empty_day(self):
        """Navigate to previous non-empty day."""
        prev_date = self.find_prev_non_empty_day(self.current_date)
        if prev_date:
            self.current_date = prev_date
            self.daily_list = self.handler.load_tasks(self.current_date)
            self.update_date_header()
            self.refresh_task_list()

    def action_next_non_empty_day(self):
        """Navigate to next non-empty day."""
        next_date = self.find_next_non_empty_day(self.current_date)
        if next_date:
            self.current_date = next_date
            self.daily_list = self.handler.load_tasks(self.current_date)
            self.update_date_header()
            self.refresh_task_list()

    def action_today(self):
        """Navigate to today."""
        self.current_date = date.today()
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.update_date_header()
        self.refresh_task_list()

    def action_show_help(self):
        """Show the help screen."""
        self.push_screen(HelpScreen())

    def parse_natural_date(self, input_str: str, from_date: date) -> date | None:
        """Parse natural language date input.

        Supports:
        - Relative offsets: +1, -1, +7, etc. (relative to from_date, the viewed date)
        - ISO format: YYYY-MM-DD (absolute)
        - Absolute words: today, tomorrow, yesterday (relative to actual current date)
        - Day names: monday, tuesday, etc. (next occurrence from actual current date)
        - Relative weeks: next week, last week (relative to actual current date)
        - Month + day: nov 10, december 25 (current year based on actual current date)
        """
        import re
        from datetime import datetime

        input_str = input_str.strip().lower()

        # Try relative offset (+1, -1, etc.)
        if input_str.startswith('+') or input_str.startswith('-'):
            try:
                days = int(input_str)
                return from_date + timedelta(days=days)
            except ValueError:
                pass

        # Try ISO format (YYYY-MM-DD)
        try:
            return date.fromisoformat(input_str)
        except ValueError:
            pass

        # Absolute date words (relative to actual current date, not viewed date)
        today = date.today()
        if input_str == "today":
            return today
        elif input_str == "tomorrow":
            return today + timedelta(days=1)
        elif input_str == "yesterday":
            return today - timedelta(days=1)
        elif input_str == "next week":
            return today + timedelta(days=7)
        elif input_str == "last week":
            return today - timedelta(days=7)

        # Day names (next occurrence)
        day_names = {
            "monday": 0, "mon": 0,
            "tuesday": 1, "tue": 1, "tues": 1,
            "wednesday": 2, "wed": 2,
            "thursday": 3, "thu": 3, "thurs": 3,
            "friday": 4, "fri": 4,
            "saturday": 5, "sat": 5,
            "sunday": 6, "sun": 6
        }

        if input_str in day_names:
            target_weekday = day_names[input_str]
            today = date.today()
            current_weekday = today.weekday()
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return today + timedelta(days=days_ahead)

        # Month + day (e.g., "nov 10", "december 25")
        month_names = {
            "jan": 1, "january": 1,
            "feb": 2, "february": 2,
            "mar": 3, "march": 3,
            "apr": 4, "april": 4,
            "may": 5,
            "jun": 6, "june": 6,
            "jul": 7, "july": 7,
            "aug": 8, "august": 8,
            "sep": 9, "sept": 9, "september": 9,
            "oct": 10, "october": 10,
            "nov": 11, "november": 11,
            "dec": 12, "december": 12
        }

        # Try to match "month day" pattern
        pattern = r'^(\w+)\s+(\d{1,2})$'
        match = re.match(pattern, input_str)
        if match:
            month_str, day_str = match.groups()
            if month_str in month_names:
                try:
                    month = month_names[month_str]
                    day = int(day_str)
                    today = date.today()
                    year = today.year
                    # Try to create the date
                    target_date = date(year, month, day)
                    # If the date is in the past, use next year
                    if target_date < today:
                        target_date = date(year + 1, month, day)
                    return target_date
                except ValueError:
                    pass

        return None

    def action_add_task(self):
        """Show input to add a new task."""
        if self.adding_task:
            return

        # Determine where and how to insert the new task
        task_widget = self.query_one(TaskListWidget)
        selected_task = task_widget.get_selected_task()

        if selected_task and selected_task.indent_level > 0:
            # Selected task is a child - insert right below it at same indent
            self.new_task_insert_index = task_widget.selected_index + 1
            self.new_task_indent_level = selected_task.indent_level
        else:
            # Selected task is a parent (or no selection) - add at bottom
            self.new_task_insert_index = None  # None means append at end
            self.new_task_indent_level = 0

        self.adding_task = True
        container = self.query_one("#input_container")
        input_widget = Input(placeholder="Enter task description...")
        container.mount(input_widget)
        input_widget.focus()

    def action_edit_task(self):
        """Edit the selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if not task or self.editing_task:
            return

        self.editing_task = True
        container = self.query_one("#input_container")
        input_widget = Input(value=task.content, placeholder="Edit task...")
        container.mount(input_widget)
        input_widget.focus()

    def action_move_task(self):
        """Move task to another day."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if not task or self.moving_task:
            return

        self.moving_task = True
        self.task_to_move = task
        container = self.query_one("#input_container")
        input_widget = Input(placeholder="Enter date (tomorrow, monday, nov 10, +1, 2025-01-15)...")
        container.mount(input_widget)
        input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission."""
        value = event.value.strip()

        if self.adding_task:
            if value:
                self.daily_list.add_task(
                    value,
                    indent_level=self.new_task_indent_level,
                    index=self.new_task_insert_index
                )
                self.save_current_tasks()
                self.refresh_task_list()
            self.adding_task = False
            # Reset insert position and indent
            self.new_task_insert_index = None
            self.new_task_indent_level = 0

        elif self.editing_task:
            if value:
                task_widget = self.query_one(TaskListWidget)
                task = task_widget.get_selected_task()
                if task:
                    task.content = value
                    self.save_current_tasks()
                    self.refresh_task_list()
            self.editing_task = False

        elif self.moving_task:
            if value and self.task_to_move:
                # Parse date input using natural language parser
                target_date = self.parse_natural_date(value, self.current_date)

                if target_date:
                    try:
                        # Move the task
                        task_widget = self.query_one(TaskListWidget)
                        moved_task = self.handler.move_task_to_date(
                            self.task_to_move,
                            self.current_date,
                            target_date
                        )

                        # Remove from current day
                        self.daily_list.remove_task(task_widget.selected_index)
                        self.save_current_tasks()
                        self.refresh_task_list()

                    except (ValueError, TypeError):
                        pass  # Error moving task, just cancel

            self.moving_task = False
            self.task_to_move = None

        # Remove input widget
        event.input.remove()

    def on_key(self, event: events.Key):
        """Handle special keys."""
        # Check if we're in an input widget - if so, don't intercept
        focused = self.focused
        if isinstance(focused, Input):
            if event.key == "escape":
                focused.remove()
                self.adding_task = False
                self.editing_task = False
                self.moving_task = False
                self.task_to_move = None
                event.prevent_default()
            return

        # Handle Tab for indent/unindent
        if event.key == "tab":
            self.action_indent()
            event.prevent_default()
            event.stop()
        elif event.key == "shift+tab":
            self.action_unindent()
            event.prevent_default()
            event.stop()

        # Handle escape to cancel any input
        elif event.key == "escape":
            container = self.query_one("#input_container")
            inputs = container.query(Input)
            if inputs:
                for input_widget in inputs:
                    input_widget.remove()
                self.adding_task = False
                self.editing_task = False
                self.moving_task = False
                self.task_to_move = None


def main():
    """Run the application."""
    app = TaskJournalApp()
    app.run()


if __name__ == "__main__":
    main()
