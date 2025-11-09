"""Data models for task management."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date, datetime


@dataclass
class Task:
    """Represents a single task.

    Tasks are organized hierarchically using indent_level, stored in a flat list.
    The folded attribute controls whether child tasks (higher indent) are visible.

    Time tracking fields:
    - estimated_seconds: User's estimate for task duration in seconds
    - actual_seconds: Accumulated time spent on task in seconds
    - timer_start: When timer was started (None if not running)
    """
    content: str
    completed: bool = False
    indent_level: int = 0
    folded: bool = False
    estimated_seconds: Optional[int] = None
    actual_seconds: int = 0
    timer_start: Optional[datetime] = None

    def toggle_complete(self):
        """Toggle completion status."""
        self.completed = not self.completed

    def toggle_fold(self):
        """Toggle fold status."""
        self.folded = not self.folded

    @staticmethod
    def _format_seconds(seconds: int) -> str:
        """Format seconds into human-readable string for markdown."""
        if seconds < 60:
            return f"{seconds}s"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0:
            parts.append(f"{secs}s")

        return "".join(parts)

    def to_markdown(self) -> str:
        """Convert task to markdown format."""
        indent = "  " * self.indent_level
        checkbox = "[x]" if self.completed else "[ ]"
        prefix = "~~" if self.completed else ""
        suffix = "~~" if self.completed else ""
        fold_marker = " <!-- folded -->" if self.folded else ""

        # Add time tracking metadata
        time_parts = []
        if self.estimated_seconds is not None:
            time_parts.append(f"est:{self._format_seconds(self.estimated_seconds)}")
        if self.actual_seconds > 0:
            time_parts.append(f"actual:{self._format_seconds(self.actual_seconds)}")

        time_marker = f" <!-- {', '.join(time_parts)} -->" if time_parts else ""

        return f"{indent}- {checkbox} {prefix}{self.content}{suffix}{fold_marker}{time_marker}"


@dataclass
class DailyTaskList:
    """Represents tasks for a specific day."""
    date: date
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, content: str, indent_level: int = 0, index: Optional[int] = None):
        """Add a new task."""
        task = Task(content=content, indent_level=indent_level)
        if index is None:
            self.tasks.append(task)
        else:
            self.tasks.insert(index, task)
        return task

    def remove_task(self, index: int):
        """Remove a task by index."""
        if 0 <= index < len(self.tasks):
            return self.tasks.pop(index)
        return None

    def move_task(self, from_index: int, to_index: int):
        """Move a task from one position to another."""
        if 0 <= from_index < len(self.tasks):
            task = self.tasks.pop(from_index)
            self.tasks.insert(to_index, task)
