"""Tests for task group operations."""
import pytest
from models import Task
from business_logic.task_operations import TaskGroupOperations


class TestTaskGroupOperations:
    """Test suite for TaskGroupOperations."""

    def test_get_task_group_single_task(self):
        """Test getting group range for a single task with no children."""
        tasks = [
            Task("Task 1", indent_level=0),
            Task("Task 2", indent_level=0),
        ]
        start, end = TaskGroupOperations.get_task_group(tasks, 0)
        assert start == 0
        assert end == 0

    def test_get_task_group_with_children(self):
        """Test getting group range for a task with children."""
        tasks = [
            Task("Parent", indent_level=0),
            Task("Child 1", indent_level=1),
            Task("Child 2", indent_level=1),
            Task("Next parent", indent_level=0),
        ]
        start, end = TaskGroupOperations.get_task_group(tasks, 0)
        assert start == 0
        assert end == 2  # Includes both children

    def test_find_prev_sibling_group_exists(self):
        """Test finding previous sibling when it exists."""
        tasks = [
            Task("Sibling 1", indent_level=0),
            Task("Sibling 2", indent_level=0),
        ]
        result = TaskGroupOperations.find_prev_sibling_group(tasks, 1)
        assert result == (0, 0)

    def test_find_prev_sibling_group_none(self):
        """Test finding previous sibling when none exists."""
        tasks = [
            Task("Only task", indent_level=0),
        ]
        result = TaskGroupOperations.find_prev_sibling_group(tasks, 0)
        assert result is None

    def test_find_next_sibling_group_exists(self):
        """Test finding next sibling when it exists."""
        tasks = [
            Task("Sibling 1", indent_level=0),
            Task("Sibling 2", indent_level=0),
        ]
        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)
        assert result == (1, 1)

    def test_find_next_sibling_group_none(self):
        """Test finding next sibling when none exists."""
        tasks = [
            Task("Only task", indent_level=0),
        ]
        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)
        assert result is None

    # TODO: Add tests for:
    # - Complex nested hierarchies
    # - Edge cases (empty list, out of bounds index)
    # - Different indent levels
