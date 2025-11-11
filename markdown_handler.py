"""Handle reading and writing tasks from/to markdown files."""
import re
from pathlib import Path
from datetime import date
from typing import Optional
from models import Task, DailyTaskList
from config import config
from utils.time_utils import parse_time_string


class MarkdownHandler:
    """Parse and write task lists in markdown format."""

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize MarkdownHandler.

        Args:
            base_dir: Optional base directory path. If None, uses config.base_dir.
        """
        if base_dir is None:
            self.base_dir = config.base_dir
        else:
            self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_file_path(self, task_date: date) -> Path:
        """Get the file path for a given date.

        Args:
            task_date: The date to get the file path for

        Returns:
            Path object pointing to the markdown file for that date (YYYY-MM-DD.md format)
        """
        filename = task_date.strftime("%Y-%m-%d.md")
        return self.base_dir / filename

    def load_tasks(self, task_date: date) -> DailyTaskList:
        """Load tasks from markdown file for a given date.

        Parses markdown file and reconstructs task objects with all metadata
        (completion status, indentation, time tracking, fold state).

        Args:
            task_date: The date to load tasks for

        Returns:
            DailyTaskList object containing all tasks for that date.
            Returns empty list if file doesn't exist or cannot be read.

        Note:
            Handles gracefully: missing files, corrupted files, encoding errors
        """
        file_path = self.get_file_path(task_date)
        daily_list = DailyTaskList(date=task_date)

        if not file_path.exists():
            return daily_list

        try:
            content = file_path.read_text()
        except (IOError, PermissionError, UnicodeDecodeError) as e:
            # File exists but can't be read (permissions, encoding issues, etc.)
            # Return empty task list rather than crashing
            return daily_list

        # Pattern to match divider lines: <!-- divider --> or <!-- divider: label -->
        divider_pattern = re.compile(r'^(\s*)<!--\s*divider(?:\s*:\s*(.+?))?\s*-->$', re.MULTILINE)

        # Pattern to match task lines: optional indent, dash, checkbox, optional strikethrough, content, optional markers
        # Matches: "  - [ ] task" or "  - [x] ~~task~~" or "  - [ ] task <!-- folded -->" or with time metadata
        task_pattern = re.compile(r'^(\s*)- \[([ x])\] (?:~~)?(.+?)(?:~~)?(?:\s*<!--.*?-->)*$', re.MULTILINE)

        # Collect all matches (dividers and tasks) with their positions
        items = []

        # Find dividers
        for match in divider_pattern.finditer(content):
            indent_str, divider_label = match.groups()
            indent_level = len(indent_str) // 2  # 2 spaces per indent level

            divider = Task(
                content=divider_label or "",
                indent_level=indent_level,
                is_divider=True
            )
            items.append((match.start(), divider))

        # Find regular tasks
        for match in task_pattern.finditer(content):
            indent_str, checkbox, task_content = match.groups()
            indent_level = len(indent_str) // 2  # 2 spaces per indent level
            completed = checkbox.lower() == 'x'

            # Check if the line contains the fold marker
            folded = '<!-- folded -->' in match.group(0)

            # Parse time metadata (est:30s, est:5m30s, actual:1h30m, etc.)
            estimated_seconds = None
            actual_seconds = 0
            # Match patterns like: est:30s, est:5m, est:1h30m15s, actual:90s
            # Updated regex to support compound time formats like 1h30m
            time_match = re.search(r'<!--\s*(?:est:([\d.]+(?:h|hr|hour|hours)?(?:\s*[\d.]+)?(?:m|min|minutes?)?(?:\s*[\d.]+)?(?:s|sec|seconds?)?))?\s*(?:,\s*)?(?:actual:([\d.]+(?:h|hr|hour|hours)?(?:\s*[\d.]+)?(?:m|min|minutes?)?(?:\s*[\d.]+)?(?:s|sec|seconds?)?))?\s*-->', match.group(0))
            if time_match:
                est_str, act_str = time_match.groups()
                if est_str:
                    estimated_seconds = parse_time_string(est_str)
                if act_str:
                    actual_seconds = parse_time_string(act_str) or 0

            # Remove all HTML comments from content (fold marker, time metadata, etc.)
            task_content_clean = re.sub(r'\s*<!--.*?-->', '', task_content).strip()

            task = Task(
                content=task_content_clean,
                completed=completed,
                indent_level=indent_level,
                folded=folded,
                estimated_seconds=estimated_seconds,
                actual_seconds=actual_seconds
            )
            items.append((match.start(), task))

        # Sort by position in file to maintain order
        items.sort(key=lambda x: x[0])

        # Add tasks and dividers in order
        for _, item in items:
            daily_list.tasks.append(item)

        return daily_list

    def save_tasks(self, daily_list: DailyTaskList):
        """Save tasks to markdown file.

        Converts task objects to markdown format with all metadata preserved.
        Creates file if it doesn't exist; overwrites if it does.

        Args:
            daily_list: The DailyTaskList to save

        Raises:
            IOError: If file cannot be written (permissions, disk full, etc.)

        Note:
            Creates empty file with date header if task list is empty.
        """
        file_path = self.get_file_path(daily_list.date)

        if not daily_list.tasks:
            # If no tasks, create an empty file or header
            content = f"# {daily_list.date.strftime('%Y-%m-%d')}\n\n"
        else:
            lines = [f"# {daily_list.date.strftime('%Y-%m-%d')}\n\n"]
            for task in daily_list.tasks:
                lines.append(task.to_markdown() + "\n")
            content = "".join(lines)

        try:
            file_path.write_text(content)
        except (IOError, PermissionError) as e:
            # Cannot write to file (permissions, disk full, etc.)
            # Raise the exception to let caller handle it
            raise IOError(f"Failed to save tasks to {file_path}: {e}") from e

    def move_task_to_date(self, task: Task, from_date: date, to_date: date):
        """Move a task from one date to another.

        Transfers a task between two date files. Resets completion status and
        actual time spent, but preserves estimates and fold state.

        Args:
            task: The task to move
            from_date: The date the task is currently on
            to_date: The date to move the task to

        Returns:
            The new task object created on the destination date

        Note:
            - Task completion is reset (uncompleted)
            - Actual time is reset (0 seconds)
            - Estimate and fold state are preserved
            - Timer is reset (timer_start = None)
        """
        # Load both task lists
        from_list = self.load_tasks(from_date)
        to_list = self.load_tasks(to_date)

        # Add task to destination (create a new task with same properties)
        new_task = Task(
            content=task.content,
            completed=task.completed,  # Preserve completion status
            indent_level=task.indent_level,
            folded=task.folded,  # Preserve fold status
            estimated_seconds=task.estimated_seconds,  # Preserve estimate
            actual_seconds=0,  # Reset actual time for new day
            timer_start=None  # Reset timer
        )
        to_list.tasks.append(new_task)

        # Save destination
        self.save_tasks(to_list)

        return new_task
