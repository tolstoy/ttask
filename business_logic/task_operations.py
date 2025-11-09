"""Task group operations for hierarchical task management.

This module provides utilities for working with parent-child task relationships
in the hierarchical task structure. Tasks are organized by indent level, where
higher indent levels represent child tasks.

Functions:
    get_task_group: Get the range of a parent and all its children
    find_prev_sibling_group: Find the previous sibling group at same indent level
    find_next_sibling_group: Find the next sibling group at same indent level
"""
from typing import List, Optional, Tuple
from models import Task


def get_task_group(tasks: List[Task], start_index: int) -> Tuple[int, int]:
    """Get the range of tasks that form a group (parent + children).

    Module-level convenience function. See TaskGroupOperations.get_task_group
    for full documentation.

    Args:
        tasks: List of all tasks
        start_index: Index of the parent task

    Returns:
        Tuple of (start_index, end_index) inclusive
    """
    return TaskGroupOperations.get_task_group(tasks, start_index)


class TaskGroupOperations:
    """Operations for managing groups of hierarchically related tasks.

    Provides utilities for working with parent-child task relationships
    in the hierarchical task structure (based on indent levels).
    """

    @staticmethod
    def get_task_group(tasks: List[Task], start_index: int) -> Tuple[int, int]:
        """
        Get the range of tasks that form a group (parent + children).

        Returns the contiguous range of indices including a parent task and all
        its direct and nested children. Children are identified by having a
        higher indent_level than the parent.

        Args:
            tasks: List of all tasks
            start_index: Index of the parent task (or leaf task)

        Returns:
            Tuple of (start_index, end_index) inclusive. Both indices point to
            valid tasks in the list.

        Example:
            >>> tasks = [Task("Parent"), Task("Child1", indent=1), Task("Child2", indent=1), Task("Next")]
            >>> TaskGroupOperations.get_task_group(tasks, 0)
            (0, 2)  # Parent at 0, children at 1-2, Next at 3 is not included
            >>> TaskGroupOperations.get_task_group(tasks, 1)
            (1, 1)  # Leaf task, only itself
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

        Searches backwards to find the nearest task at the same indent level,
        then returns its entire group (including its children).

        Args:
            tasks: List of all tasks
            index: Index of current task

        Returns:
            Tuple of (start, end) of the sibling group, or None if not found
            (e.g., current task is already the first sibling)

        Example:
            >>> tasks = [Task("Sibling1"), Task("Sibling2", indent=0)]
            >>> TaskGroupOperations.find_prev_sibling_group(tasks, 1)
            (0, 0)  # Found Sibling1
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

        Searches forwards to find the nearest task at the same indent level,
        then returns its entire group (including its children).

        Args:
            tasks: List of all tasks
            index: Index of current task

        Returns:
            Tuple of (start, end) of the sibling group, or None if not found
            (e.g., current task is already the last sibling)

        Example:
            >>> tasks = [Task("Sibling1"), Task("Sibling2", indent=0), Task("Next")]
            >>> TaskGroupOperations.find_next_sibling_group(tasks, 0)
            (1, 1)  # Found Sibling2
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
