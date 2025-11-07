"""Data models for task management."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class Task:
    """Represents a single task with optional nesting."""
    content: str
    completed: bool = False
    indent_level: int = 0
    folded: bool = False
    children: List['Task'] = field(default_factory=list)

    def toggle_complete(self):
        """Toggle completion status."""
        self.completed = not self.completed

    def toggle_fold(self):
        """Toggle fold status."""
        self.folded = not self.folded

    def to_markdown(self) -> str:
        """Convert task to markdown format."""
        indent = "  " * self.indent_level
        checkbox = "[x]" if self.completed else "[ ]"
        prefix = "~~" if self.completed else ""
        suffix = "~~" if self.completed else ""
        return f"{indent}- {checkbox} {prefix}{self.content}{suffix}"


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
