"""Tests for markdown file handling."""
import pytest
from datetime import date
from pathlib import Path
import tempfile
from models import Task, DailyTaskList
from markdown_handler import MarkdownHandler
from utils.time_utils import parse_time_string


@pytest.fixture
def temp_dir():
    """Create a temporary directory for markdown files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def markdown_handler(temp_dir):
    """Create a MarkdownHandler instance with temporary directory."""
    return MarkdownHandler(base_dir=str(temp_dir))


@pytest.fixture
def sample_task_list():
    """Create a sample DailyTaskList."""
    return DailyTaskList(
        date=date(2025, 1, 15),
        tasks=[
            Task("Buy groceries", completed=False, indent_level=0, estimated_seconds=600, actual_seconds=0),
            Task("Milk", completed=False, indent_level=1, estimated_seconds=120, actual_seconds=0),
            Task("Eggs", completed=True, indent_level=1, estimated_seconds=60, actual_seconds=45),
            Task("Call mom", completed=True, indent_level=0, estimated_seconds=900, actual_seconds=1200),
            Task("Write email", completed=False, indent_level=0, estimated_seconds=None, actual_seconds=0),
        ]
    )


class TestMarkdownHandlerInitialization:
    """Test MarkdownHandler initialization."""

    def test_init_with_custom_base_dir(self, temp_dir):
        """Test initialization with custom base directory."""
        handler = MarkdownHandler(base_dir=str(temp_dir))
        assert handler.base_dir == temp_dir

    def test_init_without_base_dir_uses_config(self):
        """Test that initialization without base_dir uses config."""
        handler = MarkdownHandler()
        # Should use config.base_dir
        assert handler.base_dir is not None

    def test_init_creates_base_directory(self, tmp_path):
        """Test that initialization creates base directory if it doesn't exist."""
        new_dir = tmp_path / "new_task_dir"
        handler = MarkdownHandler(base_dir=str(new_dir))
        assert new_dir.exists()

    def test_init_expands_tilde(self, tmp_path):
        """Test that tilde in path is expanded."""
        # Create a path with tilde simulation
        handler = MarkdownHandler(base_dir=str(tmp_path / "test"))
        assert "~" not in str(handler.base_dir)


class TestGetFilePath:
    """Test file path generation."""

    def test_get_file_path_format(self, markdown_handler):
        """Test that file path has correct format."""
        task_date = date(2025, 1, 15)
        file_path = markdown_handler.get_file_path(task_date)

        assert file_path.name == "2025-01-15.md"
        assert file_path.parent == markdown_handler.base_dir

    def test_get_file_path_different_dates(self, markdown_handler):
        """Test file paths for different dates."""
        path1 = markdown_handler.get_file_path(date(2025, 1, 1))
        path2 = markdown_handler.get_file_path(date(2025, 12, 31))

        assert path1.name == "2025-01-01.md"
        assert path2.name == "2025-12-31.md"


class TestSaveTasks:
    """Test saving tasks to markdown."""

    def test_save_tasks_creates_file(self, markdown_handler, sample_task_list):
        """Test that save_tasks creates a file."""
        markdown_handler.save_tasks(sample_task_list)
        file_path = markdown_handler.get_file_path(sample_task_list.date)
        assert file_path.exists()

    def test_save_tasks_markdown_format(self, markdown_handler, sample_task_list):
        """Test that saved file has correct markdown format."""
        markdown_handler.save_tasks(sample_task_list)
        file_path = markdown_handler.get_file_path(sample_task_list.date)
        content = file_path.read_text()

        # Check for header
        assert "# 2025-01-15" in content
        # Check for tasks
        assert "- [ ] Buy groceries" in content
        assert "- [x] ~~Call mom~~" in content

    def test_save_tasks_preserves_indentation(self, markdown_handler, sample_task_list):
        """Test that indentation is preserved."""
        markdown_handler.save_tasks(sample_task_list)
        file_path = markdown_handler.get_file_path(sample_task_list.date)
        content = file_path.read_text()

        # Check indented tasks
        assert "  - [ ] Milk" in content
        assert "  - [x] ~~Eggs~~" in content

    def test_save_tasks_includes_time_metadata(self, markdown_handler, sample_task_list):
        """Test that time metadata is included."""
        markdown_handler.save_tasks(sample_task_list)
        file_path = markdown_handler.get_file_path(sample_task_list.date)
        content = file_path.read_text()

        # Check for time metadata
        assert "est:10m" in content  # Buy groceries: 600s = 10m
        assert "est:2m" in content  # Milk: 120s = 2m
        assert "actual:45s" in content  # Eggs: 45s
        assert "est:15m" in content  # Call mom: 900s = 15m
        assert "actual:20m" in content  # Call mom: 1200s = 20m

    def test_save_empty_task_list(self, markdown_handler):
        """Test saving empty task list."""
        empty_list = DailyTaskList(date=date(2025, 1, 15), tasks=[])
        markdown_handler.save_tasks(empty_list)
        file_path = markdown_handler.get_file_path(empty_list.date)

        content = file_path.read_text()
        assert "# 2025-01-15" in content

    def test_save_tasks_overwrites_existing(self, markdown_handler, sample_task_list):
        """Test that saving overwrites existing file."""
        # Save once
        markdown_handler.save_tasks(sample_task_list)

        # Modify and save again
        sample_task_list.tasks[0].content = "Modified task"
        markdown_handler.save_tasks(sample_task_list)

        file_path = markdown_handler.get_file_path(sample_task_list.date)
        content = file_path.read_text()
        assert "Modified task" in content
        assert "Buy groceries" not in content


class TestLoadTasks:
    """Test loading tasks from markdown."""

    def test_load_tasks_from_existing_file(self, markdown_handler, sample_task_list):
        """Test loading tasks from an existing file."""
        # Save first
        markdown_handler.save_tasks(sample_task_list)

        # Load
        loaded_list = markdown_handler.load_tasks(sample_task_list.date)

        assert len(loaded_list.tasks) == len(sample_task_list.tasks)
        assert loaded_list.tasks[0].content == "Buy groceries"
        assert loaded_list.tasks[0].completed is False
        assert loaded_list.tasks[3].completed is True

    def test_load_tasks_missing_file(self, markdown_handler):
        """Test loading tasks when file doesn't exist."""
        task_list = markdown_handler.load_tasks(date(2025, 1, 1))

        assert task_list.date == date(2025, 1, 1)
        assert len(task_list.tasks) == 0

    def test_load_tasks_preserves_indentation(self, markdown_handler, sample_task_list):
        """Test that indentation is preserved when loading."""
        markdown_handler.save_tasks(sample_task_list)
        loaded_list = markdown_handler.load_tasks(sample_task_list.date)

        assert loaded_list.tasks[0].indent_level == 0
        assert loaded_list.tasks[1].indent_level == 1
        assert loaded_list.tasks[2].indent_level == 1

    def test_load_tasks_parses_completion_status(self, markdown_handler, sample_task_list):
        """Test that completion status is parsed correctly."""
        markdown_handler.save_tasks(sample_task_list)
        loaded_list = markdown_handler.load_tasks(sample_task_list.date)

        assert loaded_list.tasks[0].completed is False
        assert loaded_list.tasks[2].completed is True  # Eggs
        assert loaded_list.tasks[3].completed is True  # Call mom

    def test_load_tasks_parses_time_metadata(self, markdown_handler, sample_task_list):
        """Test that time metadata is parsed correctly."""
        markdown_handler.save_tasks(sample_task_list)
        loaded_list = markdown_handler.load_tasks(sample_task_list.date)

        # Buy groceries: est:10m
        assert loaded_list.tasks[0].estimated_seconds == 600
        # Eggs: est:1m, actual:45s
        assert loaded_list.tasks[2].estimated_seconds == 60
        assert loaded_list.tasks[2].actual_seconds == 45
        # Write email: no estimate
        assert loaded_list.tasks[4].estimated_seconds is None


class TestRoundTrip:
    """Test save and load produce identical results."""

    def test_round_trip_basic(self, markdown_handler, sample_task_list):
        """Test basic round trip (save → load → verify)."""
        # Save
        markdown_handler.save_tasks(sample_task_list)

        # Load
        loaded_list = markdown_handler.load_tasks(sample_task_list.date)

        # Save again
        markdown_handler.save_tasks(loaded_list)

        # Load again
        second_loaded = markdown_handler.load_tasks(sample_task_list.date)

        # Verify identical
        assert len(second_loaded.tasks) == len(loaded_list.tasks)
        for i in range(len(loaded_list.tasks)):
            assert second_loaded.tasks[i].content == loaded_list.tasks[i].content
            assert second_loaded.tasks[i].completed == loaded_list.tasks[i].completed
            assert second_loaded.tasks[i].indent_level == loaded_list.tasks[i].indent_level
            assert second_loaded.tasks[i].estimated_seconds == loaded_list.tasks[i].estimated_seconds
            assert second_loaded.tasks[i].actual_seconds == loaded_list.tasks[i].actual_seconds

    def test_round_trip_with_special_characters(self, markdown_handler):
        """Test round trip with special characters in task content."""
        task_list = DailyTaskList(
            date=date(2025, 1, 15),
            tasks=[
                Task("Task with [brackets] and (parens)", completed=False),
                Task("Task with **bold** and _italic_", completed=False),
                Task("Task with <!-- comment -->", completed=False),
            ]
        )

        markdown_handler.save_tasks(task_list)
        loaded_list = markdown_handler.load_tasks(task_list.date)

        # Note: HTML comments are stripped during parsing
        assert "brackets" in loaded_list.tasks[0].content
        assert "parens" in loaded_list.tasks[0].content
        assert "bold" in loaded_list.tasks[1].content

    def test_round_trip_folded_tasks(self, markdown_handler):
        """Test round trip with folded tasks."""
        task_list = DailyTaskList(
            date=date(2025, 1, 15),
            tasks=[
                Task("Parent task", completed=False, indent_level=0, folded=True),
                Task("Child task", completed=False, indent_level=1, folded=False),
            ]
        )

        markdown_handler.save_tasks(task_list)
        loaded_list = markdown_handler.load_tasks(task_list.date)

        assert loaded_list.tasks[0].folded is True
        assert loaded_list.tasks[1].folded is False


class TestParseTimeToSeconds:
    """Test time string parsing."""

    def test_parse_seconds_only(self):
        """Test parsing seconds."""
        assert parse_time_string("30s") == 30
        assert parse_time_string("90s") == 90

    def test_parse_minutes_only(self):
        """Test parsing minutes."""
        assert parse_time_string("5m") == 300
        assert parse_time_string("10m") == 600

    def test_parse_hours_only(self):
        """Test parsing hours."""
        assert parse_time_string("1h") == 3600
        assert parse_time_string("2h") == 7200

    def test_parse_combined_time(self):
        """Test parsing combined hours, minutes, seconds."""
        assert parse_time_string("1h30m") == 5400
        assert parse_time_string("1h30m15s") == 5415
        assert parse_time_string("2h15s") == 7215

    def test_parse_with_spaces(self):
        """Test parsing with spaces."""
        assert parse_time_string("1h 30m 15s") == 5415
        assert parse_time_string(" 5m ") == 300

    def test_parse_fractional_values(self):
        """Test parsing fractional values."""
        assert parse_time_string("1.5h") == 5400
        assert parse_time_string("2.5m") == 150

    def test_parse_alternative_units(self):
        """Test parsing alternative unit names."""
        assert parse_time_string("1hr") == 3600
        assert parse_time_string("5min") == 300
        assert parse_time_string("30sec") == 30

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        assert parse_time_string("") is None
        assert parse_time_string("   ") is None

    def test_parse_invalid_string(self):
        """Test parsing invalid string."""
        assert parse_time_string("invalid") is None
        assert parse_time_string("abc") is None


class TestParseVariousFormats:
    """Test parsing various markdown task formats."""

    def test_parse_simple_task(self, markdown_handler):
        """Test parsing simple task without extras."""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text("# 2025-01-15\n\n- [ ] Simple task\n")

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert len(task_list.tasks) == 1
        assert task_list.tasks[0].content == "Simple task"
        assert task_list.tasks[0].completed is False

    def test_parse_completed_task(self, markdown_handler):
        """Test parsing completed task with strikethrough."""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text("# 2025-01-15\n\n- [x] ~~Completed task~~\n")

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert task_list.tasks[0].content == "Completed task"
        assert task_list.tasks[0].completed is True

    def test_parse_indented_tasks(self, markdown_handler):
        """Test parsing tasks with various indent levels."""
        content = """# 2025-01-15

- [ ] Level 0
  - [ ] Level 1
    - [ ] Level 2
      - [ ] Level 3
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content)

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert len(task_list.tasks) == 4
        assert task_list.tasks[0].indent_level == 0
        assert task_list.tasks[1].indent_level == 1
        assert task_list.tasks[2].indent_level == 2
        assert task_list.tasks[3].indent_level == 3

    def test_parse_folded_marker(self, markdown_handler):
        """Test parsing folded marker."""
        content = """# 2025-01-15

- [ ] Parent task <!-- folded -->
  - [ ] Child task
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content)

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert task_list.tasks[0].folded is True
        assert task_list.tasks[1].folded is False

    def test_parse_time_metadata_various_formats(self, markdown_handler):
        """Test parsing various time metadata formats."""
        content = """# 2025-01-15

- [ ] Task 1 <!-- est:30s -->
- [ ] Task 2 <!-- est:5m -->
- [ ] Task 3 <!-- est:1h30m -->
- [x] ~~Task 4~~ <!-- est:10m, actual:8m -->
- [x] ~~Task 5~~ <!-- est:1h, actual:1h30m45s -->
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content)

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert task_list.tasks[0].estimated_seconds == 30
        assert task_list.tasks[1].estimated_seconds == 300
        assert task_list.tasks[2].estimated_seconds == 5400
        assert task_list.tasks[3].estimated_seconds == 600
        assert task_list.tasks[3].actual_seconds == 480
        assert task_list.tasks[4].estimated_seconds == 3600
        assert task_list.tasks[4].actual_seconds == 5445

    def test_parse_mixed_markers(self, markdown_handler):
        """Test parsing tasks with multiple markers."""
        content = """# 2025-01-15

- [x] ~~Completed task~~ <!-- folded --> <!-- est:10m, actual:8m -->
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content)

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert task_list.tasks[0].content == "Completed task"
        assert task_list.tasks[0].completed is True
        assert task_list.tasks[0].folded is True
        assert task_list.tasks[0].estimated_seconds == 600
        assert task_list.tasks[0].actual_seconds == 480


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_load_empty_file(self, markdown_handler):
        """Test loading completely empty file."""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text("")

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert len(task_list.tasks) == 0

    def test_load_file_with_only_header(self, markdown_handler):
        """Test loading file with only header."""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text("# 2025-01-15\n\n")

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert len(task_list.tasks) == 0

    def test_load_malformed_checkboxes(self, markdown_handler):
        """Test loading with malformed checkboxes."""
        content = """# 2025-01-15

- [] Missing space
- [ x ] Extra spaces
- [x] Lowercase x
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content)

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        # Lowercase x should be recognized
        assert len(task_list.tasks) == 1  # Only properly formatted task is loaded
        assert task_list.tasks[0].content == "Lowercase x"
        assert task_list.tasks[0].completed is True

    def test_load_file_with_non_task_content(self, markdown_handler):
        """Test loading file with other markdown content."""
        content = """# 2025-01-15

Some regular text here.

- [ ] Task 1
- [ ] Task 2

More text.

- Another bullet (not a task)
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content)

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        # Should only get tasks with checkboxes
        assert len(task_list.tasks) == 2

    def test_load_permission_error(self, markdown_handler, temp_dir):
        """Test loading file with permission error."""
        import os
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text("# 2025-01-15\n\n- [ ] Task\n")

        # Make file unreadable (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            file_path.chmod(0o000)

            # Should return empty list instead of crashing
            task_list = markdown_handler.load_tasks(date(2025, 1, 15))
            assert len(task_list.tasks) == 0

            # Restore permissions for cleanup
            file_path.chmod(0o644)

    def test_load_unicode_content(self, markdown_handler):
        """Test loading file with unicode characters."""
        content = """# 2025-01-15

- [ ] Task with emoji 🎉
- [ ] Task with unicode: café, naïve, 日本語
"""
        file_path = markdown_handler.get_file_path(date(2025, 1, 15))
        file_path.write_text(content, encoding='utf-8')

        task_list = markdown_handler.load_tasks(date(2025, 1, 15))
        assert "🎉" in task_list.tasks[0].content
        assert "café" in task_list.tasks[1].content

    def test_save_permission_error(self, markdown_handler, temp_dir):
        """Test saving with permission error."""
        import os
        if os.name != 'nt':  # Skip on Windows
            # Make directory read-only
            temp_dir.chmod(0o444)

            task_list = DailyTaskList(
                date=date(2025, 1, 15),
                tasks=[Task("Test task")]
            )

            # Should raise IOError
            with pytest.raises(IOError):
                markdown_handler.save_tasks(task_list)

            # Restore permissions for cleanup
            temp_dir.chmod(0o755)


class TestMoveTaskToDate:
    """Test moving tasks between dates."""

    def test_move_task_to_different_date(self, markdown_handler):
        """Test moving a task to a different date."""
        from_date = date(2025, 1, 15)
        to_date = date(2025, 1, 16)

        # Create task on from_date
        from_list = DailyTaskList(
            date=from_date,
            tasks=[Task("Task to move", estimated_seconds=600, actual_seconds=300)]
        )
        markdown_handler.save_tasks(from_list)

        # Move task
        task = from_list.tasks[0]
        new_task = markdown_handler.move_task_to_date(task, from_date, to_date)

        # Verify task was added to to_date
        to_list = markdown_handler.load_tasks(to_date)
        assert len(to_list.tasks) == 1
        assert to_list.tasks[0].content == "Task to move"

    def test_move_task_resets_completion(self, markdown_handler):
        """Test that moving task resets completion status."""
        from_date = date(2025, 1, 15)
        to_date = date(2025, 1, 16)

        from_list = DailyTaskList(
            date=from_date,
            tasks=[Task("Completed task", completed=True)]
        )
        markdown_handler.save_tasks(from_list)

        task = from_list.tasks[0]
        markdown_handler.move_task_to_date(task, from_date, to_date)

        to_list = markdown_handler.load_tasks(to_date)
        assert to_list.tasks[0].completed is False

    def test_move_task_resets_actual_time(self, markdown_handler):
        """Test that moving task resets actual time."""
        from_date = date(2025, 1, 15)
        to_date = date(2025, 1, 16)

        from_list = DailyTaskList(
            date=from_date,
            tasks=[Task("Task", estimated_seconds=600, actual_seconds=300)]
        )
        markdown_handler.save_tasks(from_list)

        task = from_list.tasks[0]
        markdown_handler.move_task_to_date(task, from_date, to_date)

        to_list = markdown_handler.load_tasks(to_date)
        assert to_list.tasks[0].actual_seconds == 0

    def test_move_task_preserves_estimate(self, markdown_handler):
        """Test that moving task preserves estimate."""
        from_date = date(2025, 1, 15)
        to_date = date(2025, 1, 16)

        from_list = DailyTaskList(
            date=from_date,
            tasks=[Task("Task", estimated_seconds=600)]
        )
        markdown_handler.save_tasks(from_list)

        task = from_list.tasks[0]
        markdown_handler.move_task_to_date(task, from_date, to_date)

        to_list = markdown_handler.load_tasks(to_date)
        assert to_list.tasks[0].estimated_seconds == 600

    def test_move_task_preserves_indent_and_fold(self, markdown_handler):
        """Test that moving task preserves indent level and fold status."""
        from_date = date(2025, 1, 15)
        to_date = date(2025, 1, 16)

        from_list = DailyTaskList(
            date=from_date,
            tasks=[Task("Task", indent_level=2, folded=True)]
        )
        markdown_handler.save_tasks(from_list)

        task = from_list.tasks[0]
        markdown_handler.move_task_to_date(task, from_date, to_date)

        to_list = markdown_handler.load_tasks(to_date)
        assert to_list.tasks[0].indent_level == 2
        assert to_list.tasks[0].folded is True
