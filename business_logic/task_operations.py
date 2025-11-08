"""Task group operations for hierarchical task management."""
from typing import List, Optional, Tuple
from models import Task


class TaskGroupOperations:
    """Operations for managing groups of hierarchically related tasks."""

    @staticmethod
    def get_task_group(tasks: List[Task], start_index: int) -> Tuple[int, int]:
        """
        Get the range of tasks that form a group (parent + children).

        Args:
            tasks: List of all tasks
            start_index: Index of the parent task

        Returns:
            Tuple of (start_index, end_index) inclusive
        """
        if start_index >= len(tasks):
            return (start_index, start_index)

        parent_indent = tasks[start_index].indent_level
        end_index = start_index

        # Find all consecutive children with higher indent
        for i in range(start_index + 1, len(tasks)):
            if tasks[i].indent_level > parent_indent:
                end_index = i
            else:
                break

        return (start_index, end_index)

    @staticmethod
    def find_prev_sibling_group(tasks: List[Task], index: int) -> Optional[Tuple[int, int]]:
        """
        Find the previous sibling group at the same indent level.

        Args:
            tasks: List of all tasks
            index: Index of current task

        Returns:
            Tuple of (start, end) of the sibling group, or None if not found
        """
        current_task = tasks[index]
        target_indent = current_task.indent_level

        # Search backwards for a task at the same indent level
        for i in range(index - 1, -1, -1):
            task = tasks[i]
            if task.indent_level == target_indent:
                # Found a sibling! Get its group range
                return TaskGroupOperations.get_task_group(tasks, i)
            elif task.indent_level < target_indent:
                # Found a parent (lower indent), no more siblings above
                return None

        return None

    @staticmethod
    def find_next_sibling_group(tasks: List[Task], index: int) -> Optional[Tuple[int, int]]:
        """
        Find the next sibling group at the same indent level.

        Args:
            tasks: List of all tasks
            index: Index of current task

        Returns:
            Tuple of (start, end) of the sibling group, or None if not found
        """
        current_task = tasks[index]
        target_indent = current_task.indent_level

        # First skip over the current task's children
        _, current_end = TaskGroupOperations.get_task_group(tasks, index)

        # Search forward from after current group
        for i in range(current_end + 1, len(tasks)):
            task = tasks[i]
            if task.indent_level == target_indent:
                # Found a sibling! Get its group range
                return TaskGroupOperations.get_task_group(tasks, i)
            elif task.indent_level < target_indent:
                # Found a task with lower indent (uncle/parent level), no more siblings
                return None

        return None
