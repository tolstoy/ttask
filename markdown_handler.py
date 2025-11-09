"""Handle reading and writing tasks from/to markdown files."""
import re
from pathlib import Path
from datetime import date
from typing import Optional
from models import Task, DailyTaskList
from config import config


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

    @staticmethod
    def _parse_time_to_seconds(time_str: str) -> int:
        """
        Parse a time string into seconds.

        Args:
            time_str: Time string like "30s", "5m", "1h30m15s"

        Returns:
            Number of seconds
        """
        time_str = time_str.strip().lower()
        if not time_str:
            return 0

        # Match patterns like: 1h30m15s, 2h, 30m, 90s
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

            return int(total_seconds)

        return 0

    def get_file_path(self, task_date: date) -> Path:
        """Get the file path for a given date."""
        filename = task_date.strftime("%Y-%m-%d.md")
        return self.base_dir / filename

    def load_tasks(self, task_date: date) -> DailyTaskList:
        """Load tasks from markdown file for a given date."""
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

        # Pattern to match task lines: optional indent, dash, checkbox, optional strikethrough, content, optional markers
        # Matches: "  - [ ] task" or "  - [x] ~~task~~" or "  - [ ] task <!-- folded -->" or with time metadata
        task_pattern = re.compile(r'^(\s*)- \[([ x])\] (?:~~)?(.+?)(?:~~)?(?:\s*<!--.*?-->)*$', re.MULTILINE)

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
            time_match = re.search(r'<!--\s*(?:est:([\d.]+(?:h|m|s|hr|min|sec|hours?|minutes?|seconds?)+))?(?:,\s*)?(?:actual:([\d.]+(?:h|m|s|hr|min|sec|hours?|minutes?|seconds?)+))?\s*-->', match.group(0))
            if time_match:
                est_str, act_str = time_match.groups()
                if est_str:
                    estimated_seconds = self._parse_time_to_seconds(est_str)
                if act_str:
                    actual_seconds = self._parse_time_to_seconds(act_str)

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
            daily_list.tasks.append(task)

        return daily_list

    def save_tasks(self, daily_list: DailyTaskList):
        """Save tasks to markdown file."""
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
        """Move a task from one date to another."""
        # Load both task lists
        from_list = self.load_tasks(from_date)
        to_list = self.load_tasks(to_date)

        # Add task to destination (create a new task with same properties)
        new_task = Task(
            content=task.content,
            completed=False,  # Reset completion status
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
