"""Main TUI application for task journal."""
from datetime import date, timedelta
from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Input
from textual.containers import Container
from textual.binding import Binding
from textual.screen import Screen
from textual import events
from markdown_handler import MarkdownHandler
from models import DailyTaskList, Task
from business_logic.date_navigator import DateNavigator, NaturalDateParser
from business_logic.task_operations import TaskGroupOperations
from business_logic.time_tracker import TimeTracker
from business_logic.scoring import ScoringSystem
from config import config
from ui.help_screen import HelpScreen
from ui.statistics_screen import StatisticsScreen
from ui.widgets import CenteredFooter
from ui.task_list_widget import TaskListWidget


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
        Binding("q", "quit", "Quit", show=False),
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
        Binding("g", "today", "Today", show=False),
        Binding("tab", "indent", "Indent", show=False),
        Binding("shift+tab", "unindent", "Unindent", show=False),
        Binding("f", "toggle_fold", "Fold", show=False),
        Binding("m", "move_task", "Move", show=False),
        Binding("r", "edit_task", "Edit", show=False),
        Binding("v", "toggle_selection_mode", "Visual", show=False),
        # Time tracking bindings
        Binding("t", "toggle_timer", "Timer", show=False),
        Binding("T", "clear_timer", "Clear Timer", show=False),
        Binding("e", "set_estimate", "Estimate", show=False),
        Binding("plus", "add_time", "Add Time", show=False),
        Binding("minus", "subtract_time", "Sub Time", show=False),
        Binding("S", "show_statistics", "Stats", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.handler = MarkdownHandler()
        self.date_navigator = DateNavigator(self.handler)
        self.time_tracker = TimeTracker()
        self.scoring_system = ScoringSystem()
        self.current_date = date.today()
        self.daily_list = self.handler.load_tasks(self.current_date)

        # Sync timer state with loaded tasks (restores timer if app was restarted)
        self.time_tracker.sync_timer_with_task_list(self.daily_list)

        self.adding_task = False
        self.editing_task = False
        self.moving_task = False
        self.task_to_move = None
        self.move_group_start = None
        self.move_group_end = None
        self.new_task_insert_index = None
        self.new_task_indent_level = 0
        # Selection mode state
        self.selection_mode = False
        self.selected_task_indices = set()
        # Time tracking state
        self.setting_estimate = False
        self.adding_time = False
        self.subtracting_time = False
        self.estimate_task_index = None
        self.time_task_index = None
        self.timer_refresh_interval = None  # For auto-refreshing timer display

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        yield Static(id="date_header")
        yield Container(
            TaskListWidget(self.daily_list, self.selection_mode, self.selected_task_indices, self.time_tracker, self.scoring_system),
            id="task_list"
        )
        yield Container(id="input_container")
        yield CenteredFooter()

    def on_mount(self) -> None:
        """Set up the app after mounting."""
        self.update_date_header()
        self.update_footer()
        # Start auto-refresh timer for live timer updates (every second)
        self.timer_refresh_interval = self.set_interval(1.0, self._refresh_timer_display)

    def _refresh_timer_display(self) -> None:
        """Refresh the task list display if a timer is running (for live seconds update)."""
        if self.time_tracker.active_task_index is not None:
            try:
                task_widget = self.query_one(TaskListWidget)
                task_widget.refresh()
            except Exception:
                # Widget not accessible (e.g., modal is open)
                # Timer keeps running in background, skip this display update
                pass

    def update_date_header(self) -> None:
        """Update the date header."""
        header = self.query_one("#date_header", Static)
        date_str = self.current_date.strftime("%A, %B %d, %Y")
        header.update(date_str)

    def update_footer(self) -> None:
        """Update the footer with selection mode status and time tracking stats."""
        try:
            footer = self.query_one(CenteredFooter)
        except Exception:
            # Footer not accessible (modal is open or transitioning)
            return

        if self.selection_mode:
            count = len(self.selected_task_indices)
            footer.update(f"[bold]VISUAL MODE[/bold] [dim]•[/dim] {count} task{'s' if count != 1 else ''} selected [dim]• Press[/dim] [bold]V[/bold] [dim]to exit[/dim]")
        else:
            # Calculate daily score and stats
            daily_score = self.scoring_system.calculate_daily_score(self.daily_list)
            streak = self.scoring_system.get_streak(self.current_date)

            # Show stats if we have any completed tasks with estimates, otherwise show help hints
            if daily_score.tasks_completed > 0 and daily_score.total_estimated_minutes > 0:
                # Format score display
                score_str = f"{int(daily_score.total_score)}pts"
                if daily_score.total_score > 0:
                    score_str = f"[green]{score_str}[/green]"
                elif daily_score.total_score < 0:
                    score_str = f"[red]{score_str}[/red]"

                # Format streak display
                streak_str = f"[yellow]{streak}[/yellow]d" if streak > 0 else "0d"

                # Efficiency percentage (lower is better)
                efficiency_pct = int(daily_score.efficiency_ratio * 100)

                footer.update(f"Score: {score_str} [dim]•[/dim] Streak: {streak_str} [dim]•[/dim] {daily_score.tasks_completed} tasks [dim]•[/dim] Eff: {efficiency_pct}% [dim]•[/dim] [bold]H[/bold] [dim]Help[/dim] [bold]Q[/bold] [dim]Quit[/dim]")
            else:
                # No stats yet, show helpful hints
                footer.update("[dim]Press[/dim] [bold]H[/bold] [dim]for Help[/dim] [dim]•[/dim] [bold]Q[/bold] [dim]to Quit[/dim]")

    def refresh_task_list(self) -> None:
        """Refresh the task list widget."""
        task_widget = self.query_one(TaskListWidget)
        task_widget.daily_list = self.daily_list
        task_widget.selection_mode = self.selection_mode
        task_widget.selected_task_indices = self.selected_task_indices
        task_widget.time_tracker = self.time_tracker
        task_widget.scoring_system = self.scoring_system

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

        # Update footer to show selection mode status
        self.update_footer()

    def save_current_tasks(self) -> None:
        """Save the current task list."""
        self.handler.save_tasks(self.daily_list)

    def save_and_refresh(self) -> None:
        """Save current tasks and refresh the UI display.

        Helper method to reduce duplication of the common pattern:
        save_current_tasks() followed by refresh_task_list().
        """
        self.save_current_tasks()
        self.refresh_task_list()

    def action_move_down(self) -> None:
        """Move selection down."""
        task_widget = self.query_one(TaskListWidget)
        task_widget.move_selection(1)

    def action_move_up(self) -> None:
        """Move selection up."""
        task_widget = self.query_one(TaskListWidget)
        task_widget.move_selection(-1)

    def action_toggle_complete(self) -> None:
        """Toggle completion of selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if task:
            task.toggle_complete()
            self.save_and_refresh()

    def action_delete_task(self) -> None:
        """Delete the selected task(s) and all their children."""
        task_widget = self.query_one(TaskListWidget)
        if not self.daily_list.tasks:
            return

        if self.selection_mode and self.selected_task_indices:
            # Delete all selected tasks (already includes children due to auto-selection)
            # Sort in reverse order to maintain indices while deleting
            for idx in sorted(self.selected_task_indices, reverse=True):
                if idx < len(self.daily_list.tasks):
                    self.daily_list.remove_task(idx)

            # Clear selection after deleting
            self.selected_task_indices.clear()
        else:
            # Normal mode: delete current task and all its children
            start_idx, end_idx = TaskGroupOperations.get_task_group(
                self.daily_list.tasks, task_widget.selected_index
            )

            # Delete all tasks in the group (in reverse to maintain indices)
            for i in range(end_idx, start_idx - 1, -1):
                self.daily_list.remove_task(i)

        self.save_and_refresh()

    def action_indent(self) -> None:
        """Indent the selected task and all its children."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if not task:
            return

        # Get the task group (parent + all children)
        start_idx, end_idx = TaskGroupOperations.get_task_group(
            self.daily_list.tasks, task_widget.selected_index
        )

        # Find the maximum indent level in the group
        max_group_indent = max(
            self.daily_list.tasks[i].indent_level
            for i in range(start_idx, end_idx + 1)
        )

        # Only indent if the deepest child won't exceed max indent level
        if max_group_indent < config.max_indent_level:
            # Indent all tasks in the group
            for i in range(start_idx, end_idx + 1):
                self.daily_list.tasks[i].indent_level += 1
            self.save_and_refresh()

    def action_unindent(self) -> None:
        """Unindent the selected task and all its children."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if not task or task.indent_level == 0:
            return

        # Get the task group (parent + all children)
        start_idx, end_idx = TaskGroupOperations.get_task_group(
            self.daily_list.tasks, task_widget.selected_index
        )

        # Unindent all tasks in the group
        for i in range(start_idx, end_idx + 1):
            self.daily_list.tasks[i].indent_level -= 1
        self.save_and_refresh()

    def action_toggle_fold(self) -> None:
        """Toggle fold status of selected task."""
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()
        if task and task_widget.has_children(task_widget.selected_index):
            task.toggle_fold()
            self.save_and_refresh()

    def action_move_task_up(self) -> None:
        """Move selected task (and its children) up, only within same indent level."""
        task_widget = self.query_one(TaskListWidget)
        if task_widget.selected_index <= 0:
            return

        # Get current task group
        current_start, current_end = TaskGroupOperations.get_task_group(
            self.daily_list.tasks, task_widget.selected_index
        )

        # Find previous sibling at the same indent level
        prev_group = TaskGroupOperations.find_prev_sibling_group(
            self.daily_list.tasks, task_widget.selected_index
        )
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
        self.save_and_refresh()

    def action_move_task_down(self) -> None:
        """Move selected task (and its children) down, only within same indent level."""
        task_widget = self.query_one(TaskListWidget)

        # Get current task group
        current_start, current_end = TaskGroupOperations.get_task_group(
            self.daily_list.tasks, task_widget.selected_index
        )

        # Find next sibling at the same indent level
        next_group = TaskGroupOperations.find_next_sibling_group(
            self.daily_list.tasks, task_widget.selected_index
        )
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
        self.save_and_refresh()

    def action_next_day(self) -> None:
        """Navigate to next day."""
        # Save current day's tasks before switching (preserves timer state in file)
        self.save_current_tasks()

        self.current_date += timedelta(days=1)
        self.daily_list = self.handler.load_tasks(self.current_date)

        # Sync timer state with newly loaded day
        self.time_tracker.sync_timer_with_task_list(self.daily_list)

        # Exit selection mode when changing days
        self.selection_mode = False
        self.selected_task_indices.clear()
        self.update_date_header()
        self.refresh_task_list()

    def action_prev_day(self) -> None:
        """Navigate to previous day."""
        # Save current day's tasks before switching (preserves timer state in file)
        self.save_current_tasks()

        self.current_date -= timedelta(days=1)
        self.daily_list = self.handler.load_tasks(self.current_date)

        # Sync timer state with newly loaded day
        self.time_tracker.sync_timer_with_task_list(self.daily_list)

        # Exit selection mode when changing days
        self.selection_mode = False
        self.selected_task_indices.clear()
        self.update_date_header()
        self.refresh_task_list()

    def action_prev_non_empty_day(self) -> None:
        """Navigate to previous non-empty day."""
        prev_date = self.date_navigator.find_prev_non_empty_day(self.current_date)
        if prev_date:
            # Save current day's tasks before switching (preserves timer state in file)
            self.save_current_tasks()

            self.current_date = prev_date
            self.daily_list = self.handler.load_tasks(self.current_date)

            # Sync timer state with newly loaded day
            self.time_tracker.sync_timer_with_task_list(self.daily_list)

            # Exit selection mode when changing days
            self.selection_mode = False
            self.selected_task_indices.clear()
            self.update_date_header()
            self.refresh_task_list()

    def action_next_non_empty_day(self) -> None:
        """Navigate to next non-empty day."""
        next_date = self.date_navigator.find_next_non_empty_day(self.current_date)
        if next_date:
            # Save current day's tasks before switching (preserves timer state in file)
            self.save_current_tasks()

            self.current_date = next_date
            self.daily_list = self.handler.load_tasks(self.current_date)

            # Sync timer state with newly loaded day
            self.time_tracker.sync_timer_with_task_list(self.daily_list)

            # Exit selection mode when changing days
            self.selection_mode = False
            self.selected_task_indices.clear()
            self.update_date_header()
            self.refresh_task_list()

    def action_today(self) -> None:
        """Navigate to today."""
        # Save current day's tasks before switching (preserves timer state in file)
        self.save_current_tasks()

        self.current_date = date.today()
        self.daily_list = self.handler.load_tasks(self.current_date)

        # Sync timer state with newly loaded day
        self.time_tracker.sync_timer_with_task_list(self.daily_list)

        # Exit selection mode when changing days
        self.selection_mode = False
        self.selected_task_indices.clear()
        self.update_date_header()
        self.refresh_task_list()

    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())

    def action_toggle_selection_mode(self) -> None:
        """Toggle visual selection mode."""
        self.selection_mode = not self.selection_mode
        if not self.selection_mode:
            # Exiting selection mode - clear selections
            self.selected_task_indices.clear()
        self.refresh_task_list()

    def get_task_and_children_indices(self, parent_index: int) -> list[int]:
        """Get indices of a task and all its children.

        Args:
            parent_index: Index of the parent task

        Returns:
            List of indices including parent and all children
        """
        if parent_index < 0 or parent_index >= len(self.daily_list.tasks):
            return []

        start_idx, end_idx = TaskGroupOperations.get_task_group(
            self.daily_list.tasks, parent_index
        )
        return list(range(start_idx, end_idx + 1))

    def action_toggle_task_selection(self) -> None:
        """Toggle selection of current task (and all children if parent)."""
        if not self.selection_mode:
            return

        task_widget = self.query_one(TaskListWidget)
        if not self.daily_list.tasks:
            return

        # Get all indices for this task and its children
        indices_to_toggle = self.get_task_and_children_indices(task_widget.selected_index)

        # Check if the parent is already selected
        parent_selected = task_widget.selected_index in self.selected_task_indices

        if parent_selected:
            # Deselect parent and all children
            for idx in indices_to_toggle:
                self.selected_task_indices.discard(idx)
        else:
            # Select parent and all children
            for idx in indices_to_toggle:
                self.selected_task_indices.add(idx)

        self.refresh_task_list()

    def action_add_task(self) -> None:
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

    def action_edit_task(self) -> None:
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

    @staticmethod
    def parse_time_string(time_str: str) -> Optional[int]:
        """
        Parse a time string into seconds.

        Supports formats:
        - Plain number: "30" → 30 minutes → 1800 seconds
        - Seconds: "90s" or "90sec" → 90 seconds
        - Minutes: "30m" or "30min" → 1800 seconds
        - Hours: "2h" → 7200 seconds
        - Combined: "1h30m15s" → 5415 seconds
        - Decimal: "1.5h" → 5400 seconds, "2.5m" → 150 seconds

        Returns:
            Number of seconds, or None if parse fails
        """
        import re

        time_str = time_str.strip().lower()
        if not time_str:
            return None

        # Try plain number first (assumes minutes, convert to seconds)
        try:
            return int(time_str) * 60
        except ValueError:
            pass

        # Try to parse with units
        # Match patterns like: 1h30m15s, 2h, 30m, 90s, 1.5h, etc.
        # Pattern: optional hours, optional minutes, optional seconds
        pattern = r'(?:(\d+(?:\.\d+)?)(?:h|hr|hour|hours))?\s*(?:(\d+(?:\.\d+)?)(?:m|min|minutes?))?\s*(?:(\d+(?:\.\d+)?)(?:s|sec|seconds?))?'
        match = re.match(pattern, time_str)

        if match:
            hours_str, minutes_str, seconds_str = match.groups()
            total_seconds = 0.0

            if hours_str:
                total_seconds += float(hours_str) * 3600
            if minutes_str:
                total_seconds += float(minutes_str) * 60
            if seconds_str:
                total_seconds += float(seconds_str)

            if total_seconds > 0:
                return int(total_seconds)

        return None

    def action_move_task(self) -> None:
        """Move task(s) and all their children to another day."""
        task_widget = self.query_one(TaskListWidget)
        if self.moving_task:
            return

        if self.selection_mode and self.selected_task_indices:
            # Moving multiple selected tasks
            if not self.selected_task_indices:
                return

            # Store the selected indices for later
            # Use sorted list to maintain proper order when moving
            self.moving_task = True
            self.move_group_start = None  # Signal that we're using selected tasks
            self.move_group_end = None
        else:
            # Moving single task and its children
            task = task_widget.get_selected_task()
            if not task:
                return

            # Get the task group (parent + all children)
            start_idx, end_idx = TaskGroupOperations.get_task_group(
                self.daily_list.tasks, task_widget.selected_index
            )

            # Store the group indices for later
            self.moving_task = True
            self.task_to_move = task  # Keep for backwards compatibility
            self.move_group_start = start_idx
            self.move_group_end = end_idx

        container = self.query_one("#input_container")
        input_widget = Input(placeholder="Enter date (tomorrow, monday, nov 10, +1, 2025-01-15)...")
        container.mount(input_widget)
        input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        value = event.value.strip()

        if self.adding_task:
            if value:
                self.daily_list.add_task(
                    value,
                    indent_level=self.new_task_indent_level,
                    index=self.new_task_insert_index
                )
                self.save_and_refresh()
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
                    self.save_and_refresh()
            self.editing_task = False

        elif self.moving_task:
            if value:
                # Parse date input using natural language parser
                target_date = NaturalDateParser.parse(value, self.current_date)

                if target_date:
                    try:
                        # Check if we're moving selected tasks or a single group
                        if self.move_group_start is None:
                            # Moving selected tasks (selection mode)
                            tasks_to_move = [self.daily_list.tasks[i] for i in sorted(self.selected_task_indices)
                                           if i < len(self.daily_list.tasks)]

                            for task in tasks_to_move:
                                self.handler.move_task_to_date(
                                    task,
                                    self.current_date,
                                    target_date
                                )

                            # Remove selected tasks from current day (in reverse order)
                            for i in sorted(self.selected_task_indices, reverse=True):
                                if i < len(self.daily_list.tasks):
                                    self.daily_list.remove_task(i)

                            # Clear selection after moving
                            self.selected_task_indices.clear()
                        else:
                            # Moving single task group (normal mode)
                            tasks_to_move = self.daily_list.tasks[self.move_group_start:self.move_group_end + 1]

                            for task in tasks_to_move:
                                self.handler.move_task_to_date(
                                    task,
                                    self.current_date,
                                    target_date
                                )

                            # Remove all tasks in the group from current day (in reverse)
                            for i in range(self.move_group_end, self.move_group_start - 1, -1):
                                self.daily_list.remove_task(i)

                        self.save_and_refresh()

                    except (ValueError, TypeError, IOError) as e:
                        # Error moving task (invalid date, file I/O error, etc.)
                        # Silently cancel the operation - task remains in place
                        pass

            self.moving_task = False
            self.task_to_move = None
            self.move_group_start = None
            self.move_group_end = None

        elif self.setting_estimate:
            if value:
                seconds = self.parse_time_string(value)
                if seconds is not None and 0 <= self.estimate_task_index < len(self.daily_list.tasks):
                    task = self.daily_list.tasks[self.estimate_task_index]
                    task.estimated_seconds = seconds
                    self.save_and_refresh()
            self.setting_estimate = False
            self.estimate_task_index = None

        elif self.adding_time:
            if value:
                seconds = self.parse_time_string(value)
                if seconds is not None and 0 <= self.time_task_index < len(self.daily_list.tasks):
                    task = self.daily_list.tasks[self.time_task_index]
                    self.time_tracker.add_manual_time(task, seconds)
                    self.save_and_refresh()
            self.adding_time = False
            self.time_task_index = None

        elif self.subtracting_time:
            if value:
                seconds = self.parse_time_string(value)
                if seconds is not None and 0 <= self.time_task_index < len(self.daily_list.tasks):
                    task = self.daily_list.tasks[self.time_task_index]
                    self.time_tracker.add_manual_time(task, -seconds)  # Negative to subtract
                    self.save_and_refresh()
            self.subtracting_time = False
            self.time_task_index = None

        # Remove input widget
        event.input.remove()

    def action_toggle_timer(self) -> None:
        """
        Toggle timer for the selected task.

        How it works:
        - Press 't' on a task to START the timer (shows ⏱️ icon and live elapsed time)
        - Press 't' again to STOP the timer (adds elapsed time to actual_minutes)
        - Stopping one timer automatically happens if you start another
        - Timer continues running even if you switch tasks or days
        """
        if not self.daily_list.tasks:
            return

        task_widget = self.query_one(TaskListWidget)
        task = self.daily_list.tasks[task_widget.selected_index]

        is_running, seconds_added = self.time_tracker.toggle_timer(
            self.daily_list,
            task_widget.selected_index
        )

        self.save_and_refresh()

        # Force immediate timer display update to sync with timer start
        if is_running:
            self._refresh_timer_display()

    def action_clear_timer(self) -> None:
        """
        Clear all time tracking from the selected task.

        Removes:
        - Running timer (if any)
        - Time estimate
        - Actual time accumulated

        Use this to completely reset time tracking for a task.
        Press Shift+T to clear.
        """
        if not self.daily_list.tasks:
            return

        task_widget = self.query_one(TaskListWidget)
        task = self.daily_list.tasks[task_widget.selected_index]

        # Clear timer if running
        self.time_tracker.clear_timer(self.daily_list)

        # Clear all time tracking data
        task.estimated_seconds = None
        task.actual_seconds = 0
        task.timer_start = None

        self.save_and_refresh()

        # Show feedback AFTER save_and_refresh
        footer = self.query_one(CenteredFooter)
        footer.update(f"[red]Time tracking cleared:[/red] {task.content[:50]}")

        # Reset footer after 3 seconds
        self.set_timer(3.0, self.update_footer)

    def action_set_estimate(self) -> None:
        """Set or edit estimate for the selected task."""
        if not self.daily_list.tasks:
            return

        task_widget = self.query_one(TaskListWidget)
        task = self.daily_list.tasks[task_widget.selected_index]

        # Show input for estimate
        container = self.query_one("#input_container")

        # Format current estimate for display
        current_est = ""
        if task.estimated_seconds:
            if task.estimated_seconds < 60:
                current_est = f" [current: {task.estimated_seconds}s]"
            else:
                mins = task.estimated_seconds // 60
                secs = task.estimated_seconds % 60
                if secs > 0:
                    current_est = f" [current: {mins}m{secs}s]"
                else:
                    current_est = f" [current: {mins}m]"

        input_widget = Input(
            placeholder=f"Enter estimate (e.g., 30, 90s, 1h30m){current_est}" if current_est else "Enter estimate (e.g., 30, 90s, 1h30m)"
        )
        container.mount(input_widget)
        input_widget.focus()

        # Mark that we're setting estimate
        self.setting_estimate = True
        self.estimate_task_index = task_widget.selected_index

    def action_add_time(self) -> None:
        """Manually add time to the selected task."""
        if not self.daily_list.tasks:
            return

        task_widget = self.query_one(TaskListWidget)

        # Show input for time to add
        container = self.query_one("#input_container")
        input_widget = Input(placeholder="Add time (e.g., 15, 90s, 30m, 1h)")
        container.mount(input_widget)
        input_widget.focus()

        # Mark that we're adding time
        self.adding_time = True
        self.time_task_index = task_widget.selected_index

    def action_subtract_time(self) -> None:
        """Manually subtract time from the selected task."""
        if not self.daily_list.tasks:
            return

        task_widget = self.query_one(TaskListWidget)

        # Show input for time to subtract
        container = self.query_one("#input_container")
        input_widget = Input(placeholder="Subtract time (e.g., 15, 90s, 30m, 1h)")
        container.mount(input_widget)
        input_widget.focus()

        # Mark that we're subtracting time
        self.subtracting_time = True
        self.time_task_index = task_widget.selected_index

    def action_show_statistics(self) -> None:
        """Show the statistics modal screen."""
        daily_score = self.scoring_system.calculate_daily_score(self.daily_list)
        streak = self.scoring_system.get_streak(self.current_date)
        self.push_screen(StatisticsScreen(daily_score, streak, self.scoring_system))

    def on_key(self, event: events.Key) -> None:
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
                self.setting_estimate = False
                self.adding_time = False
                self.subtracting_time = False
                self.estimate_task_index = None
                self.time_task_index = None
                event.prevent_default()
            return

        # Handle Space and x - context-aware based on selection mode
        if event.key == "space" or event.key == "x":
            if self.selection_mode:
                self.action_toggle_task_selection()
            else:
                self.action_toggle_complete()
            event.prevent_default()
            event.stop()

        # Handle Tab for indent/unindent
        elif event.key == "tab":
            self.action_indent()
            event.prevent_default()
            event.stop()
        elif event.key == "shift+tab":
            self.action_unindent()
            event.prevent_default()
            event.stop()

        # Handle escape to cancel any input
        elif event.key == "escape":
            # Don't handle escape if a modal screen is active
            if len(self.screen_stack) > 1:
                return
            container = self.query_one("#input_container")
            inputs = container.query(Input)
            if inputs:
                for input_widget in inputs:
                    input_widget.remove()
                self.adding_task = False
                self.editing_task = False
                self.moving_task = False
                self.task_to_move = None
                self.setting_estimate = False
                self.adding_time = False
                self.subtracting_time = False
                self.estimate_task_index = None
                self.time_task_index = None


def main():
    """Run the application."""
    app = TaskJournalApp()
    app.run()


if __name__ == "__main__":
    main()
