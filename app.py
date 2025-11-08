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
from config import config
from ui.help_screen import HelpScreen
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
        background: transparent;
        color: #0abdc6;
        border: thick #0abdc6;
    }

    #date_header {
        height: 3;
        content-align: center middle;
        background: transparent;
        color: #0abdc6;
        text-style: bold;
        border: thick #0abdc6;
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
        self.date_navigator = DateNavigator(self.handler)
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

    def update_date_header(self) -> None:
        """Update the date header."""
        header = self.query_one("#date_header", Static)
        date_str = self.current_date.strftime("%A, %B %d, %Y")
        header.update(date_str)

    def refresh_task_list(self) -> None:
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
        """Delete the selected task."""
        task_widget = self.query_one(TaskListWidget)
        if self.daily_list.tasks:
            self.daily_list.remove_task(task_widget.selected_index)
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
        self.current_date += timedelta(days=1)
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.update_date_header()
        self.refresh_task_list()

    def action_prev_day(self) -> None:
        """Navigate to previous day."""
        self.current_date -= timedelta(days=1)
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.update_date_header()
        self.refresh_task_list()

    def action_prev_non_empty_day(self) -> None:
        """Navigate to previous non-empty day."""
        prev_date = self.date_navigator.find_prev_non_empty_day(self.current_date)
        if prev_date:
            self.current_date = prev_date
            self.daily_list = self.handler.load_tasks(self.current_date)
            self.update_date_header()
            self.refresh_task_list()

    def action_next_non_empty_day(self) -> None:
        """Navigate to next non-empty day."""
        next_date = self.date_navigator.find_next_non_empty_day(self.current_date)
        if next_date:
            self.current_date = next_date
            self.daily_list = self.handler.load_tasks(self.current_date)
            self.update_date_header()
            self.refresh_task_list()

    def action_today(self) -> None:
        """Navigate to today."""
        self.current_date = date.today()
        self.daily_list = self.handler.load_tasks(self.current_date)
        self.update_date_header()
        self.refresh_task_list()

    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())

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

    def action_move_task(self) -> None:
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
            if value and self.task_to_move:
                # Parse date input using natural language parser
                target_date = NaturalDateParser.parse(value, self.current_date)

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
                        self.save_and_refresh()

                    except (ValueError, TypeError, IOError) as e:
                        # Error moving task (invalid date, file I/O error, etc.)
                        # Silently cancel the operation - task remains in place
                        pass

            self.moving_task = False
            self.task_to_move = None

        # Remove input widget
        event.input.remove()

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
