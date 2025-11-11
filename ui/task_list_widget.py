"""Task list widget for displaying and navigating tasks."""
import re
from typing import Optional, TYPE_CHECKING
from textual.widgets import Static
from models import DailyTaskList, Task
from utils.time_utils import format_time

if TYPE_CHECKING:
    from business_logic.time_tracker import TimeTracker
    from business_logic.scoring import ScoringSystem


class TaskListWidget(Static):
    """Widget to display the list of tasks."""

    def __init__(self, daily_list: DailyTaskList, selection_mode: bool = False, selected_task_indices: set = None, time_tracker: Optional['TimeTracker'] = None, scoring_system: Optional['ScoringSystem'] = None):
        super().__init__()
        self.daily_list = daily_list
        self.selected_index = 0
        self.selection_mode = selection_mode
        self.selected_task_indices = selected_task_indices or set()
        self.time_tracker = time_tracker
        self.scoring_system = scoring_system

    def format_time_display(self, task: Task, task_index: int) -> str:
        """
        Format time tracking display for a task.

        Returns Rich-formatted string like:
        - Active timer: [yellow][1:23/30m][/yellow] (shows live M:SS)
        - Completed, beat estimate: [green][30m→25m +12][/green]
        - Completed, over estimate: [red][30m→28m45s -7][/red]
        - Has estimate only: [dim][est:30m][/dim]
        """
        if not self.time_tracker or not self.scoring_system or task.is_divider:
            return ""

        # Check if timer is running for this task
        is_timer_running = self.time_tracker.is_timer_running(task_index)

        # Don't show anything if no estimate, no actual time, and timer isn't running
        if task.estimated_seconds is None and task.actual_seconds == 0 and not is_timer_running:
            return ""

        if is_timer_running:
            # Show elapsed time in M:SS format for live feedback
            elapsed_seconds = self.time_tracker.get_elapsed_seconds(task)
            elapsed_minutes = elapsed_seconds // 60
            elapsed_secs = elapsed_seconds % 60

            # Show previously accumulated time if any
            if task.actual_seconds > 0:
                elapsed_str = f"{elapsed_minutes}:{elapsed_secs:02d} (+{format_time(task.actual_seconds)})"
            else:
                elapsed_str = f"{elapsed_minutes}:{elapsed_secs:02d}"

            est_str = format_time(task.estimated_seconds) if task.estimated_seconds else "??"
            return f" [yellow]\\[{elapsed_str}/{est_str}][/yellow]"

        # If task is completed and has estimate, show score
        if task.completed and task.estimated_seconds is not None:
            score = self.scoring_system.calculate_task_score(task)
            score_str = f"+{int(score)}" if score >= 0 else f"{int(score)}"

            est_str = format_time(task.estimated_seconds)
            act_str = format_time(task.actual_seconds)

            if task.actual_seconds <= task.estimated_seconds:
                # Beat the estimate
                return f" [green]\\[{est_str}→{act_str} {score_str}][/green]"
            else:
                # Over estimate
                return f" [red]\\[{est_str}→{act_str} {score_str}][/red]"

        # Just has estimate or actual time
        parts = []
        if task.estimated_seconds is not None:
            parts.append(f"est:{format_time(task.estimated_seconds)}")
        if task.actual_seconds > 0:
            parts.append(f"act:{format_time(task.actual_seconds)}")

        if parts:
            return f" [dim]\\[{', '.join(parts)}][/dim]"

        return ""

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

    def should_show_divider_before(self, index: int) -> bool:
        """Check if a divider should be shown before this task.

        A divider is shown when:
        - This is the first completed task at this indent level
        - Within the current parent context (or top-level if no parent)
        - There are incomplete tasks before it at the same level
        """
        if index >= len(self.daily_list.tasks):
            return False

        task = self.daily_list.tasks[index]

        # Only show divider before completed tasks
        if not task.completed:
            return False

        # Find parent context
        parent_index = None
        for i in range(index - 1, -1, -1):
            if self.daily_list.tasks[i].indent_level < task.indent_level:
                parent_index = i
                break

        # Look backwards for tasks at the same indent level
        for i in range(index - 1, -1, -1):
            prev_task = self.daily_list.tasks[i]

            # Stop if we reach a parent level (lower indent)
            if prev_task.indent_level < task.indent_level:
                # We've reached parent level without finding a same-level task
                # This means we're the first task at this level - no divider
                return False

            # Only consider tasks at the same indent level
            if prev_task.indent_level == task.indent_level:
                # Found a same-level task before us
                if not prev_task.completed:
                    # Found an incomplete task at same level - show divider!
                    return True
                else:
                    # Found another completed task - no divider (already past it)
                    return False

        # No same-level tasks found before us - no divider
        return False

    def get_vertical_lines(self, index: int) -> list:
        """Get vertical line characters showing parent-child hierarchy.

        For each indent level before the current task, determines if a vertical
        line (│) should be shown to indicate we're still within that parent's children.

        Args:
            index: Index of the task to get vertical lines for

        Returns:
            List of strings, one per indent level, each being "   │" or "    " (4 chars)
            Example: ["   │", "   │"] for a task at indent 2 with both parents having more children
        """
        if index >= len(self.daily_list.tasks):
            return []

        from business_logic.task_operations import TaskGroupOperations

        current_task = self.daily_list.tasks[index]
        current_indent = current_task.indent_level

        if current_indent == 0:
            return []  # Top-level tasks have no vertical lines

        lines = []

        # For each indent level from 0 to current-1
        for level in range(current_indent):
            # Find the most recent parent at this level
            parent_index = None
            for i in range(index - 1, -1, -1):
                if self.daily_list.tasks[i].indent_level == level:
                    parent_index = i
                    break

            if parent_index is not None:
                # Check if this parent's children extend past the current task
                _, group_end = TaskGroupOperations.get_task_group(
                    self.daily_list.tasks, parent_index
                )

                # Show vertical line for all children (including last child)
                if index <= group_end and index > parent_index:
                    lines.append("   │")
                else:
                    lines.append("    ")
            else:
                # No parent found at this level (shouldn't happen in valid hierarchy)
                lines.append("    ")

        return lines

    def wrap_text(self, text: str, width: int) -> list[str]:
        """Wrap text to fit within width, preserving Rich markup.

        Args:
            text: The text to wrap (may contain Rich markup tags)
            width: Maximum width for each line

        Returns:
            List of wrapped lines (without indentation - that's added during rendering)
        """
        if width <= 10:  # Minimum reasonable width
            return [text]  # Can't wrap meaningfully, return as-is

        # Simple word-based wrapping
        words = text.split()
        if not words:
            return [""]

        lines = []
        current_line = words[0]  # Start with first word

        for word in words[1:]:  # Iterate from second word onwards
            # Calculate visible length by removing ALL Rich markup tags
            # Pattern matches [anything] or [/anything]
            visible_current = re.sub(r'\[/?[^\]]*\]', '', current_line)
            visible_word = re.sub(r'\[/?[^\]]*\]', '', word)

            # Check if adding this word (with a space) would exceed width
            if len(visible_current) + 1 + len(visible_word) <= width:
                current_line = f"{current_line} {word}"
            else:
                # Line would be too long, save current line and start new one
                lines.append(current_line)
                current_line = word

        # Add the last line
        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def render(self) -> str:
        """Render the task list."""
        if not self.daily_list.tasks:
            return "[dim]No tasks for today. Press 'a' to add one.[/dim]"

        # Get available width for wrapping (accounting for padding and scrollbar)
        # Try multiple sources for width, with fallback to conservative default
        available_width = 80  # Conservative default
        try:
            # Try to get scrollable content region (excludes padding, border, scrollbar)
            if self.parent and hasattr(self.parent, 'scrollable_content_region'):
                available_width = self.parent.scrollable_content_region.width
            # Fall back to parent container width minus padding and scrollbar
            elif self.parent and hasattr(self.parent, 'size') and self.parent.size:
                available_width = self.parent.size.width - 6  # -4 padding, -2 scrollbar
            # Last resort: console width
            elif hasattr(self, 'app') and hasattr(self.app, 'console'):
                available_width = self.app.console.width - 6
        except (AttributeError, TypeError):
            pass  # Use default

        lines = []
        skip_until_indent = None

        for i, task in enumerate(self.daily_list.tasks):
            # Skip children of folded tasks
            if skip_until_indent is not None:
                if task.indent_level > skip_until_indent:
                    continue
                else:
                    skip_until_indent = None

            # Check if we need to show a divider before this task
            if self.should_show_divider_before(i):
                # Get vertical lines for hierarchy
                divider_vertical_lines = self.get_vertical_lines(i)

                # Build indent with vertical lines (each segment is already 4 chars)
                divider_indent_with_lines = ""
                for line_segment in divider_vertical_lines:
                    divider_indent_with_lines += line_segment

                if task.indent_level == 0:
                    # Main divider (top-level): thicker line, standard indentation
                    # marker (1) + selection_indicator (1) + space (1)
                    divider_prefix = "   "
                    prefix_length = len(divider_prefix)
                    divider_width = max(10, available_width - prefix_length)
                    divider_line = f"{divider_prefix}[dim]{'━' * divider_width}[/dim]"
                else:
                    # Child divider: align with checkbox position
                    # Layer vertical lines and divider with separate formatting to avoid artifacts
                    # marker (1) + selection_indicator (1) + space (1) + indent_with_lines + fold_indicator (2)
                    prefix_length = 3 + len(divider_indent_with_lines) + 2
                    divider_width = max(10, available_width - prefix_length)
                    divider_line = f"   [dim]{divider_indent_with_lines}[/dim]  [dim]{'─' * divider_width}[/dim]"

                lines.append(divider_line)

            # Selection marker
            marker = ">" if i == self.selected_index else " "

            # Selection indicator (✓ for selected tasks in selection mode)
            selection_indicator = ""
            if self.selection_mode and i in self.selected_task_indices:
                selection_indicator = "✓"
            else:
                selection_indicator = " "

            # Get vertical lines for hierarchy (returns list of "   │" or "    " per level)
            vertical_lines = self.get_vertical_lines(i)

            # Build indent with vertical lines (each segment is already 4 chars)
            indent_with_lines = ""
            for line_segment in vertical_lines:
                indent_with_lines += line_segment

            # Handle dividers differently
            if task.is_divider:
                # Render divider line
                prefix_length = 1 + 1 + 1 + len(indent_with_lines)  # marker + selection + space + indent
                divider_width = max(10, available_width - prefix_length)

                # Create divider line with optional label
                if task.content:
                    # Divider with label: "┄┄┄ Label ┄┄┄"
                    label_with_spaces = f" {task.content} "
                    remaining_width = divider_width - len(label_with_spaces)
                    left_dashes = remaining_width // 2
                    right_dashes = remaining_width - left_dashes
                    divider_content = f"{'┄' * left_dashes}{label_with_spaces}{'┄' * right_dashes}"
                else:
                    # Divider without label: just dashes
                    divider_content = '┄' * divider_width

                # Apply purple color
                if i == self.selected_index:
                    divider_line = f"[#ff006e on #2d2d44]{marker}{selection_indicator} [dim]{indent_with_lines}[/dim][#8b5cf6]{divider_content}[/#8b5cf6][/#ff006e on #2d2d44]"
                else:
                    divider_line = f"{marker}{selection_indicator} [dim]{indent_with_lines}[/dim][#8b5cf6]{divider_content}[/#8b5cf6]"

                lines.append(divider_line)
                continue  # Skip normal task rendering

            # Add fold indicator - always use 2 chars for consistent alignment
            fold_indicator = "  "  # Default: two spaces
            if self.has_children(i):
                if task.folded:
                    fold_indicator = "▶ "
                    skip_until_indent = task.indent_level
                else:
                    fold_indicator = "▼ "

            # Escape brackets so they're not interpreted as markup
            checkbox = "\\[x]" if task.completed else "\\[ ]"

            # Add time tracking display
            time_display = self.format_time_display(task, i)
            task_content_with_time = task.content + time_display

            # Calculate prefix length (visible characters before content)
            # marker (1) + selection_indicator (1) + space (1) + indent_with_lines + fold_indicator (2) + checkbox (3) + space (1)
            prefix_length = 1 + 1 + 1 + len(indent_with_lines) + 2 + 3 + 1

            # Calculate available width for content
            # Ensure we have at least 20 chars for content, otherwise don't wrap
            if available_width - prefix_length < 20:
                # Terminal too narrow for meaningful wrapping
                wrapped_lines = [task_content_with_time]
            else:
                content_width = available_width - prefix_length
                # Wrap the content (returns plain wrapped lines without indent)
                wrapped_lines = self.wrap_text(task_content_with_time, content_width)

            # Apply strikethrough if completed
            if task.completed:
                wrapped_lines = [f"[strike]{line}[/strike]" for line in wrapped_lines]

            # Render first line with full prefix
            if i == self.selected_index:
                first_line = f"[#ff006e on #2d2d44]{marker}{selection_indicator} [dim]{indent_with_lines}[/dim][#0abdc6]{fold_indicator}[/#0abdc6]{checkbox} {wrapped_lines[0]}[/#ff006e on #2d2d44]"
            else:
                first_line = f"{marker}{selection_indicator} [dim]{indent_with_lines}[/dim][#0abdc6]{fold_indicator}[/#0abdc6]{checkbox} {wrapped_lines[0]}"

            lines.append(first_line)

            # Add continuation lines with proper indentation including vertical lines
            # marker (1) + selection_indicator (1) + space (1) + indent_with_lines + fold (2) + checkbox (3) + space (1)
            continuation_indent = "   " + indent_with_lines + "      "
            for continuation in wrapped_lines[1:]:
                if i == self.selected_index:
                    cont_line = f"[#ff006e on #2d2d44] {selection_indicator} [dim]{indent_with_lines}[/dim]      {continuation}[/#ff006e on #2d2d44]"
                else:
                    cont_line = f" {selection_indicator} [dim]{indent_with_lines}[/dim]      {continuation}"
                lines.append(cont_line)

        return "\n".join(lines)

    def get_visible_line_number(self, task_index: int) -> int:
        """Get the visible line number for a task index (accounting for folded tasks and wrapping)."""
        visible_line = 0
        skip_until_indent = None

        # Get available width for wrapping calculation (accounting for padding and scrollbar)
        # Try multiple sources for width, with fallback to conservative default
        available_width = 80  # Conservative default
        try:
            # Try to get scrollable content region (excludes padding, border, scrollbar)
            if self.parent and hasattr(self.parent, 'scrollable_content_region'):
                available_width = self.parent.scrollable_content_region.width
            # Fall back to parent container width minus padding and scrollbar
            elif self.parent and hasattr(self.parent, 'size') and self.parent.size:
                available_width = self.parent.size.width - 6  # -4 padding, -2 scrollbar
            # Last resort: console width
            elif hasattr(self, 'app') and hasattr(self.app, 'console'):
                available_width = self.app.console.width - 6
        except (AttributeError, TypeError):
            pass  # Use default

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

            # Check if we need to account for a divider before this task
            if self.should_show_divider_before(i):
                visible_line += 1  # Divider takes up one line

            # Check if this task has children and is folded
            if self.has_children(i) and task.folded:
                skip_until_indent = task.indent_level

            # If this is our target task, return the current visible line
            if i == task_index:
                return visible_line

            # Calculate how many lines this task occupies (accounting for wrapping)
            # Must match the logic in render() method
            line_vertical_lines = self.get_vertical_lines(i)
            # Build indent with vertical lines (each segment is already 4 chars)
            line_indent_with_lines = ""
            for line_segment in line_vertical_lines:
                line_indent_with_lines += line_segment

            # marker (1) + selection_indicator (1) + space (1) + indent_with_lines + fold_indicator (2) + checkbox (3) + space (1)
            prefix_length = 1 + 1 + 1 + len(line_indent_with_lines) + 2 + 3 + 1

            # Add time tracking display (must match render())
            time_display = self.format_time_display(task, i)
            task_content_with_time = task.content + time_display

            # Same width validation as render()
            if available_width - prefix_length < 20:
                # Terminal too narrow, no wrapping
                wrapped_lines = [task_content_with_time]
            else:
                content_width = available_width - prefix_length
                wrapped_lines = self.wrap_text(task_content_with_time, content_width)

            visible_line += len(wrapped_lines)

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
                    # Selected task is above viewport, scroll up to show it at top
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
