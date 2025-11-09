"""Task sorting and reordering logic for completed/incomplete separation.

This module handles automatic reordering of tasks when they are completed or uncompleted.
Tasks are sorted with incomplete tasks above completed tasks, with dividers shown at
each indent level.
"""
from typing import List, Optional, Tuple
from models import Task


class TaskSorter:
    """Handles sorting and reordering of tasks based on completion status."""

    @staticmethod
    def find_parent_context(tasks: List[Task], index: int) -> Tuple[Optional[int], int, int]:
        """Find the parent context for a task.

        Args:
            tasks: List of all tasks
            index: Index of the task to find context for

        Returns:
            Tuple of (parent_index, sibling_start, sibling_end):
            - parent_index: Index of parent task, or None if top-level
            - sibling_start: First index of sibling group (inclusive)
            - sibling_end: Last index of sibling group (exclusive)
        """
        if index >= len(tasks):
            return None, 0, len(tasks)

        current_indent = tasks[index].indent_level

        # If top-level (indent 0), siblings are all other top-level tasks
        if current_indent == 0:
            return None, 0, len(tasks)

        # Find parent (first task before us with lower indent)
        parent_index = None
        for i in range(index - 1, -1, -1):
            if tasks[i].indent_level < current_indent:
                parent_index = i
                break

        if parent_index is None:
            # No parent found, treat as top-level
            return None, 0, len(tasks)

        parent_indent = tasks[parent_index].indent_level
        target_child_indent = parent_indent + 1

        # Find range of children at the same indent level as current task
        sibling_start = parent_index + 1
        sibling_end = parent_index + 1

        # Find all children of parent
        for i in range(parent_index + 1, len(tasks)):
            if tasks[i].indent_level <= parent_indent:
                # Reached next task at parent level or above
                break
            sibling_end = i + 1

        return parent_index, sibling_start, sibling_end

    @staticmethod
    def find_completion_boundary(tasks: List[Task], start: int, end: int,
                                  target_indent: int) -> Optional[int]:
        """Find the index where incomplete tasks end and completed tasks begin.

        Only considers tasks at the target_indent level within the given range.

        Args:
            tasks: List of all tasks
            start: Start of range to search (inclusive)
            end: End of range to search (exclusive)
            target_indent: Only consider tasks at this indent level

        Returns:
            Index of first completed task at target_indent, or None if all incomplete
        """
        # Scan through range, looking only at tasks with target indent
        for i in range(start, end):
            if i >= len(tasks):
                break

            task = tasks[i]

            # Only examine tasks at the target indent level (skip children)
            if task.indent_level == target_indent and task.completed:
                return i

        return None

    @staticmethod
    def find_target_index_for_completion(tasks: List[Task], index: int,
                                         completing: bool) -> int:
        """Find the target index when toggling task completion.

        Args:
            tasks: List of all tasks
            index: Index of task being toggled
            completing: True if marking as complete, False if marking incomplete

        Returns:
            Target index where the task group should be moved
        """
        if index >= len(tasks):
            return index

        from business_logic.task_operations import TaskGroupOperations

        current_task = tasks[index]
        current_indent = current_task.indent_level

        # Get the group we're moving (to exclude from boundary search)
        group_start, group_end = TaskGroupOperations.get_task_group(tasks, index)

        # Find parent context
        parent_index, sibling_start, sibling_end = TaskSorter.find_parent_context(
            tasks, index
        )

        if completing:
            # Moving to completed section (bottom of all tasks at this level)
            # Find the last task group at this indent level
            last_at_indent = None
            i = sibling_start
            while i < sibling_end:
                if i >= len(tasks):
                    break
                if tasks[i].indent_level == current_indent:
                    # Skip the group we're moving
                    if i >= group_start and i <= group_end:
                        i = group_end + 1
                        continue
                    last_at_indent = i
                    # Skip this task's group
                    _, group_end_i = TaskGroupOperations.get_task_group(tasks, i)
                    i = group_end_i + 1
                else:
                    i += 1

            # Return position after the last task group at this level
            if last_at_indent is not None and last_at_indent < len(tasks):
                _, last_group_end = TaskGroupOperations.get_task_group(
                    tasks, last_at_indent
                )
                return last_group_end + 1
            return sibling_end

        else:
            # Moving to incomplete section (bottom of incomplete tasks)
            # Find where completed tasks start (excluding the task we're moving)
            boundary = None
            i = sibling_start
            while i < sibling_end:
                if i >= len(tasks):
                    break

                task = tasks[i]

                # Skip the group we're moving
                if i >= group_start and i <= group_end:
                    i = group_end + 1
                    continue

                # Only examine tasks at the target indent level
                if task.indent_level == current_indent and task.completed:
                    boundary = i
                    break

                i += 1

            if boundary is None:
                # No completed tasks (other than the one we're moving)
                # Go to end of siblings
                return sibling_end
            else:
                # Insert right before first completed task
                return boundary

    @staticmethod
    def reorder_task_on_completion(tasks: List[Task], index: int) -> Optional[int]:
        """Reorder a task when its completion status is toggled.

        This should be called AFTER the task's completion status has been toggled.

        Args:
            tasks: List of all tasks (will be modified in place)
            index: Index of the task that was toggled

        Returns:
            New index of the task after reordering, or None if no move needed
        """
        if index >= len(tasks):
            return None

        current_task = tasks[index]

        # Determine where the task should go
        target_index = TaskSorter.find_target_index_for_completion(
            tasks, index, current_task.completed
        )

        # Get the entire group that needs to move
        from business_logic.task_operations import TaskGroupOperations
        group_start, group_end = TaskGroupOperations.get_task_group(tasks, index)

        # If already in the right position, no move needed
        if target_index >= group_start and target_index <= group_end + 1:
            return index

        # Extract the group
        group_size = group_end - group_start + 1
        moving_tasks = []
        for _ in range(group_size):
            moving_tasks.append(tasks.pop(group_start))

        # Adjust target index if needed (if we removed tasks before target)
        if group_start < target_index:
            target_index -= group_size

        # Insert at target position
        for i, task in enumerate(moving_tasks):
            tasks.insert(target_index + i, task)

        return target_index
