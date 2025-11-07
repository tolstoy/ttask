"""Handle reading and writing tasks from/to markdown files."""
import re
from pathlib import Path
from datetime import date
from typing import Optional
from models import Task, DailyTaskList


class MarkdownHandler:
    """Parse and write task lists in markdown format."""

    def __init__(self, base_dir: str = "~/tasks"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

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

        content = file_path.read_text()

        # Pattern to match task lines: optional indent, dash, checkbox, optional strikethrough, content
        # Matches: "  - [ ] task" or "  - [x] ~~task~~"
        task_pattern = re.compile(r'^(\s*)- \[([ x])\] (?:~~)?(.+?)(?:~~)?$', re.MULTILINE)

        for match in task_pattern.finditer(content):
            indent_str, checkbox, task_content = match.groups()
            indent_level = len(indent_str) // 2  # 2 spaces per indent level
            completed = checkbox.lower() == 'x'

            task = Task(
                content=task_content.strip(),
                completed=completed,
                indent_level=indent_level
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

        file_path.write_text(content)

    def move_task_to_date(self, task: Task, from_date: date, to_date: date):
        """Move a task from one date to another."""
        # Load both task lists
        from_list = self.load_tasks(from_date)
        to_list = self.load_tasks(to_date)

        # Add task to destination (create a new task with same properties)
        new_task = Task(
            content=task.content,
            completed=False,  # Reset completion status
            indent_level=task.indent_level
        )
        to_list.tasks.append(new_task)

        # Save destination
        self.save_tasks(to_list)

        return new_task
