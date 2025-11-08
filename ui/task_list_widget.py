"""Task list widget for displaying and navigating tasks."""
from typing import Optional
from textual.widgets import Static
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

    def move_selection(self, delta: int) -> None:
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

    def scroll_to_selected(self) -> None:
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
        except (AttributeError, RuntimeError) as e:
            # Scrolling failed (widget not ready or container issues)
            # This can happen during rapid UI updates, safe to ignore
            pass

    def get_selected_task(self) -> Optional[Task]:
        """Get the currently selected task."""
        if 0 <= self.selected_index < len(self.daily_list.tasks):
            return self.daily_list.tasks[self.selected_index]
        return None
