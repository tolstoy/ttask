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

    def test_get_task_group_deeply_nested(self):
        """Test getting a group with deeply nested children."""
        tasks = [
            Task("Parent", indent_level=0),
            Task("Child", indent_level=1),
            Task("Grandchild", indent_level=2),
            Task("Great-grandchild", indent_level=3),
            Task("Another Parent", indent_level=0),
        ]
        start, end = TaskGroupOperations.get_task_group(tasks, 0)
        assert start == 0
        assert end == 3  # All descendants

    def test_get_task_group_middle_child(self):
        """Test getting a group starting from a middle child."""
        tasks = [
            Task("Parent", indent_level=0),
            Task("Child 1", indent_level=1),
            Task("Grandchild", indent_level=2),
            Task("Child 2", indent_level=1),
        ]
        # Get group for Child 1 (includes its grandchild)
        start, end = TaskGroupOperations.get_task_group(tasks, 1)
        assert start == 1
        assert end == 2

    def test_get_task_group_last_item(self):
        """Test getting a group for the last item."""
        tasks = [
            Task("Task 1", indent_level=0),
            Task("Task 2", indent_level=0),
        ]
        start, end = TaskGroupOperations.get_task_group(tasks, 1)
        assert start == 1
        assert end == 1

    def test_find_prev_sibling_group_with_children(self):
        """Test finding previous sibling group that has children."""
        tasks = [
            Task("Parent 1", indent_level=0),
            Task("Child 1.1", indent_level=1),
            Task("Parent 2", indent_level=0),
            Task("Child 2.1", indent_level=1),
        ]
        result = TaskGroupOperations.find_prev_sibling_group(tasks, 2)  # Parent 2
        assert result is not None
        assert result == (0, 1)  # Parent 1 and its child

    def test_find_prev_sibling_group_skip_different_indent(self):
        """Test that find_prev_sibling skips tasks at different indent levels."""
        tasks = [
            Task("Parent", indent_level=0),
            Task("Child 1", indent_level=1),
            Task("Grandchild", indent_level=2),
            Task("Child 2", indent_level=1),
        ]
        # Looking for prev sibling of Child 2 should find Child 1 group
        result = TaskGroupOperations.find_prev_sibling_group(tasks, 3)
        assert result is not None
        assert result == (1, 2)  # Child 1 and Grandchild

    def test_find_next_sibling_group_with_children(self):
        """Test finding next sibling group that has children."""
        tasks = [
            Task("Parent 1", indent_level=0),
            Task("Child 1.1", indent_level=1),
            Task("Parent 2", indent_level=0),
            Task("Child 2.1", indent_level=1),
        ]
        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)  # Parent 1
        assert result is not None
        assert result == (2, 3)  # Parent 2 and its child

    def test_find_next_sibling_group_skip_children(self):
        """Test that find_next_sibling skips children and finds actual siblings."""
        tasks = [
            Task("Parent 1", indent_level=0),
            Task("Child 1", indent_level=1),
            Task("Grandchild", indent_level=2),
            Task("Parent 2", indent_level=0),
        ]
        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)  # Parent 1
        assert result is not None
        assert result == (3, 3)  # Parent 2 (no children)

    def test_complex_nested_hierarchy(self):
        """Test complex multi-level hierarchy."""
        tasks = [
            Task("Root 1", indent_level=0),
            Task("Level 1.1", indent_level=1),
            Task("Level 2.1", indent_level=2),
            Task("Level 1.2", indent_level=1),
            Task("Root 2", indent_level=0),
            Task("Level 1.3", indent_level=1),
        ]
        # Get Root 1 group should include all its descendants
        start, end = TaskGroupOperations.get_task_group(tasks, 0)
        assert start == 0
        assert end == 3

        # Find next sibling of Root 1 should be Root 2
        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)
        assert result == (4, 5)

    def test_edge_case_single_task(self):
        """Test operations with single task."""
        tasks = [Task("Only task", indent_level=0)]
        start, end = TaskGroupOperations.get_task_group(tasks, 0)
        assert start == 0
        assert end == 0

        result = TaskGroupOperations.find_prev_sibling_group(tasks, 0)
        assert result is None

        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)
        assert result is None

    def test_multiple_children_at_same_level(self):
        """Test parent with multiple children at the same indent level."""
        tasks = [
            Task("Parent", indent_level=0),
            Task("Child 1", indent_level=1),
            Task("Child 2", indent_level=1),
            Task("Child 3", indent_level=1),
            Task("Next Parent", indent_level=0),
        ]
        start, end = TaskGroupOperations.get_task_group(tasks, 0)
        assert start == 0
        assert end == 3  # Parent + 3 children

    def test_find_sibling_among_complex_structure(self):
        """Test finding siblings in a complex mixed-indent structure."""
        tasks = [
            Task("A", indent_level=0),
            Task("A.1", indent_level=1),
            Task("A.1.1", indent_level=2),
            Task("A.2", indent_level=1),
            Task("B", indent_level=0),
            Task("B.1", indent_level=1),
            Task("C", indent_level=0),
        ]
        # Find next sibling of A should be B
        result = TaskGroupOperations.find_next_sibling_group(tasks, 0)
        assert result == (4, 5)

        # Find next sibling of B should be C
        result = TaskGroupOperations.find_next_sibling_group(tasks, 4)
        assert result == (6, 6)
