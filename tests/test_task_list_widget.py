"""Tests for TaskListWidget."""
import pytest
from datetime import date
from models import Task, DailyTaskList
from ui.task_list_widget import TaskListWidget


@pytest.fixture
def simple_list():
    """Simple flat list of tasks."""
    tasks = [
        Task("Task 1", completed=False, indent_level=0),
        Task("Task 2", completed=True, indent_level=0),
        Task("Task 3", completed=False, indent_level=0),
    ]
    return DailyTaskList(date=date.today(), tasks=tasks)


@pytest.fixture
def nested_list():
    """Nested task list with parent-child relationships."""
    tasks = [
        Task("Parent 1", completed=False, indent_level=0, folded=False),
        Task("Child 1.1", completed=False, indent_level=1),
        Task("Child 1.2", completed=True, indent_level=1),
        Task("Parent 2", completed=False, indent_level=0, folded=False),
        Task("Child 2.1", completed=False, indent_level=1),
    ]
    return DailyTaskList(date=date.today(), tasks=tasks)


@pytest.fixture
def folded_list():
    """List with folded parent tasks."""
    tasks = [
        Task("Parent 1", completed=False, indent_level=0, folded=True),
        Task("Child 1.1", completed=False, indent_level=1),
        Task("Child 1.2", completed=True, indent_level=1),
        Task("Parent 2", completed=False, indent_level=0, folded=False),
        Task("Child 2.1", completed=False, indent_level=1),
    ]
    return DailyTaskList(date=date.today(), tasks=tasks)


@pytest.fixture
def deeply_nested_list():
    """Deeply nested task list (3 levels)."""
    tasks = [
        Task("Level 0", completed=False, indent_level=0, folded=False),
        Task("Level 1", completed=False, indent_level=1, folded=False),
        Task("Level 2", completed=False, indent_level=2),
        Task("Level 1 again", completed=False, indent_level=1),
    ]
    return DailyTaskList(date=date.today(), tasks=tasks)


class TestTaskListWidget:
    """Test suite for TaskListWidget."""

    def test_init(self, simple_list):
        """Test widget initialization."""
        widget = TaskListWidget(simple_list)
        assert widget.daily_list == simple_list
        assert widget.selected_index == 0

    def test_has_children_true(self, nested_list):
        """Test has_children returns True for parents."""
        widget = TaskListWidget(nested_list)
        assert widget.has_children(0) is True  # Parent 1 has children
        assert widget.has_children(3) is True  # Parent 2 has children

    def test_has_children_false(self, nested_list):
        """Test has_children returns False for leaf nodes."""
        widget = TaskListWidget(nested_list)
        assert widget.has_children(1) is False  # Child 1.1
        assert widget.has_children(2) is False  # Child 1.2
        assert widget.has_children(4) is False  # Child 2.1 (last item)

    def test_has_children_last_item(self, nested_list):
        """Test has_children returns False for last item."""
        widget = TaskListWidget(nested_list)
        assert widget.has_children(4) is False

    def test_is_task_visible_all_visible(self, nested_list):
        """Test all tasks visible when nothing is folded."""
        widget = TaskListWidget(nested_list)
        for i in range(len(nested_list.tasks)):
            assert widget.is_task_visible(i) is True

    def test_is_task_visible_folded_parent(self, folded_list):
        """Test children hidden when parent is folded."""
        widget = TaskListWidget(folded_list)
        assert widget.is_task_visible(0) is True   # Parent 1 (folded)
        assert widget.is_task_visible(1) is False  # Child 1.1 (hidden)
        assert widget.is_task_visible(2) is False  # Child 1.2 (hidden)
        assert widget.is_task_visible(3) is True   # Parent 2 (not folded)
        assert widget.is_task_visible(4) is True   # Child 2.1 (visible)

    def test_is_task_visible_out_of_bounds(self, simple_list):
        """Test is_task_visible returns False for out of bounds indices."""
        widget = TaskListWidget(simple_list)
        assert widget.is_task_visible(-1) is False
        assert widget.is_task_visible(10) is False

    def test_render_empty_list(self, empty_daily_list):
        """Test rendering an empty task list."""
        widget = TaskListWidget(empty_daily_list)
        output = widget.render()
        assert "No tasks for today" in output
        assert "Press 'a' to add one" in output

    def test_render_simple_list(self, simple_list):
        """Test rendering a simple task list."""
        widget = TaskListWidget(simple_list)
        output = widget.render()
        assert "Task 1" in output
        assert "Task 2" in output
        assert "Task 3" in output
        assert ">" in output  # Selection marker

    def test_render_completed_task_strikethrough(self, simple_list):
        """Test completed tasks have strikethrough."""
        widget = TaskListWidget(simple_list)
        output = widget.render()
        assert "[strike]Task 2[/strike]" in output  # Task 2 is completed

    def test_render_fold_indicators(self, nested_list):
        """Test fold indicators appear for parent tasks."""
        widget = TaskListWidget(nested_list)
        output = widget.render()
        assert "▼" in output  # Unfolded indicator

    def test_render_folded_indicator(self, folded_list):
        """Test folded indicator appears."""
        widget = TaskListWidget(folded_list)
        output = widget.render()
        assert "▶" in output  # Folded indicator

    def test_render_indentation(self, nested_list):
        """Test tasks are indented correctly."""
        widget = TaskListWidget(nested_list)
        widget.daily_list.tasks[1].indent_level = 2  # Make Child 1.1 more indented
        output = widget.render()
        lines = output.split("\n")
        # Lines with higher indent should have more spaces
        assert "    " in output  # Double indent (2 spaces * 2)

    def test_get_visible_line_number_no_folding(self, simple_list):
        """Test visible line numbers without folding."""
        widget = TaskListWidget(simple_list)
        assert widget.get_visible_line_number(0) == 0
        assert widget.get_visible_line_number(1) == 1
        assert widget.get_visible_line_number(2) == 2

    def test_get_visible_line_number_with_folding(self, folded_list):
        """Test visible line numbers with folded tasks."""
        widget = TaskListWidget(folded_list)
        assert widget.get_visible_line_number(0) == 0  # Parent 1
        # Children 1.1 and 1.2 are hidden, so they shouldn't increment visible line
        assert widget.get_visible_line_number(3) == 1  # Parent 2 (next visible)
        assert widget.get_visible_line_number(4) == 2  # Child 2.1

    def test_move_selection_down(self, simple_list):
        """Test moving selection down."""
        widget = TaskListWidget(simple_list)
        widget.selected_index = 0
        widget.move_selection(1)
        assert widget.selected_index == 1

    def test_move_selection_up(self, simple_list):
        """Test moving selection up."""
        widget = TaskListWidget(simple_list)
        widget.selected_index = 2
        widget.move_selection(-1)
        assert widget.selected_index == 1

    def test_move_selection_bounds_bottom(self, simple_list):
        """Test selection doesn't go past bottom."""
        widget = TaskListWidget(simple_list)
        widget.selected_index = 2  # Last item
        widget.move_selection(1)
        assert widget.selected_index == 2  # Stays at last item

    def test_move_selection_bounds_top(self, simple_list):
        """Test selection doesn't go past top."""
        widget = TaskListWidget(simple_list)
        widget.selected_index = 0
        widget.move_selection(-1)
        assert widget.selected_index == 0  # Stays at first item

    def test_move_selection_skip_hidden_tasks(self, folded_list):
        """Test selection skips hidden tasks."""
        widget = TaskListWidget(folded_list)
        widget.selected_index = 0  # Parent 1 (folded)
        widget.move_selection(1)
        # Should skip hidden children (indices 1, 2) and go to Parent 2 (index 3)
        assert widget.selected_index == 3

    def test_move_selection_empty_list(self, empty_daily_list):
        """Test move_selection on empty list doesn't crash."""
        widget = TaskListWidget(empty_daily_list)
        widget.move_selection(1)  # Should not crash
        assert widget.selected_index == 0

    def test_get_selected_task(self, simple_list):
        """Test getting the selected task."""
        widget = TaskListWidget(simple_list)
        widget.selected_index = 1
        task = widget.get_selected_task()
        assert task is not None
        assert task.content == "Task 2"

    def test_get_selected_task_invalid_index(self, simple_list):
        """Test get_selected_task returns None for invalid index."""
        widget = TaskListWidget(simple_list)
        widget.selected_index = 99
        assert widget.get_selected_task() is None

    def test_get_selected_task_empty_list(self, empty_daily_list):
        """Test get_selected_task returns None for empty list."""
        widget = TaskListWidget(empty_daily_list)
        assert widget.get_selected_task() is None

    def test_deeply_nested_visibility(self, deeply_nested_list):
        """Test visibility with deeply nested tasks."""
        widget = TaskListWidget(deeply_nested_list)
        # All visible initially
        for i in range(len(deeply_nested_list.tasks)):
            assert widget.is_task_visible(i) is True

        # Fold Level 1 (index 1)
        deeply_nested_list.tasks[1].folded = True
        assert widget.is_task_visible(0) is True   # Level 0
        assert widget.is_task_visible(1) is True   # Level 1 (folded)
        assert widget.is_task_visible(2) is False  # Level 2 (hidden)
        assert widget.is_task_visible(3) is True   # Level 1 again (visible)

        # Fold Level 0 (index 0) - should hide everything below
        deeply_nested_list.tasks[0].folded = True
        assert widget.is_task_visible(0) is True   # Level 0 (folded)
        assert widget.is_task_visible(1) is False  # Level 1 (hidden)
        assert widget.is_task_visible(2) is False  # Level 2 (hidden)
        assert widget.is_task_visible(3) is False  # Level 1 again (hidden)
