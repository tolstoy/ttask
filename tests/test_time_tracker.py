"""Tests for time tracking functionality."""
import pytest
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import tempfile
from models import Task, DailyTaskList
from business_logic.time_tracker import TimeTracker


@pytest.fixture
def temp_state_file():
    """Create a temporary file for timer state."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def time_tracker(temp_state_file):
    """Create a TimeTracker instance with temporary state file."""
    return TimeTracker(state_file=temp_state_file)


@pytest.fixture
def task_list_with_tasks():
    """Create a DailyTaskList with sample tasks."""
    return DailyTaskList(
        date=date.today(),
        tasks=[
            Task("Task 1", estimated_seconds=300, actual_seconds=0),
            Task("Task 2", estimated_seconds=600, actual_seconds=100),
            Task("Task 3", estimated_seconds=None, actual_seconds=50),
        ]
    )


class TestTimeTrackerInitialization:
    """Test TimeTracker initialization and state management."""

    def test_init_creates_default_state_file(self):
        """Test that initialization creates default state file path."""
        tracker = TimeTracker()
        assert tracker.state_file == Path.home() / ".taskjournal" / "timer_state.json"
        assert tracker.active_task_index is None
        assert tracker.active_task_date is None
        assert tracker.timer_start_timestamp is None

    def test_init_with_custom_state_file(self, temp_state_file):
        """Test initialization with custom state file."""
        tracker = TimeTracker(state_file=temp_state_file)
        assert tracker.state_file == temp_state_file

    def test_init_creates_parent_directory(self, tmp_path):
        """Test that initialization creates parent directory if needed."""
        state_file = tmp_path / "subdir" / "timer_state.json"
        tracker = TimeTracker(state_file=state_file)
        assert state_file.parent.exists()


class TestTimerStartStop:
    """Test starting and stopping timers."""

    def test_start_timer_valid_task(self, time_tracker, task_list_with_tasks):
        """Test starting timer on a valid task."""
        result = time_tracker.start_timer(task_list_with_tasks, 0)
        assert result is True
        assert time_tracker.active_task_index == 0
        assert time_tracker.active_task_date == task_list_with_tasks.date.isoformat()
        assert time_tracker.timer_start_timestamp is not None
        assert task_list_with_tasks.tasks[0].timer_start is not None

    def test_start_timer_invalid_index(self, time_tracker, task_list_with_tasks):
        """Test starting timer with invalid task index."""
        result = time_tracker.start_timer(task_list_with_tasks, 99)
        assert result is False
        assert time_tracker.active_task_index is None

    def test_start_timer_negative_index(self, time_tracker, task_list_with_tasks):
        """Test starting timer with negative index."""
        result = time_tracker.start_timer(task_list_with_tasks, -1)
        assert result is False

    def test_stop_timer_accumulates_time(self, time_tracker, task_list_with_tasks):
        """Test that stopping timer accumulates time."""
        # Start timer
        time_tracker.start_timer(task_list_with_tasks, 0)
        initial_actual = task_list_with_tasks.tasks[0].actual_seconds

        # Wait a moment (simulate time passing)
        import time
        time.sleep(0.1)

        # Stop timer
        seconds_accumulated = time_tracker.stop_timer(task_list_with_tasks)

        assert seconds_accumulated >= 0
        assert task_list_with_tasks.tasks[0].actual_seconds >= initial_actual
        assert task_list_with_tasks.tasks[0].timer_start is None
        assert time_tracker.active_task_index is None

    def test_stop_timer_when_no_timer_running(self, time_tracker, task_list_with_tasks):
        """Test stopping timer when no timer is running."""
        result = time_tracker.stop_timer(task_list_with_tasks)
        assert result == 0

    def test_start_timer_stops_previous_timer(self, time_tracker, task_list_with_tasks):
        """Test that starting a timer stops the previously running timer."""
        # Start timer on task 0
        time_tracker.start_timer(task_list_with_tasks, 0)
        import time
        time.sleep(0.1)

        # Start timer on task 1 (should stop task 0's timer)
        time_tracker.start_timer(task_list_with_tasks, 1)

        assert task_list_with_tasks.tasks[0].timer_start is None
        assert task_list_with_tasks.tasks[1].timer_start is not None
        assert time_tracker.active_task_index == 1


class TestTimerToggle:
    """Test timer toggle functionality."""

    def test_toggle_starts_timer(self, time_tracker, task_list_with_tasks):
        """Test toggle starts timer when not running."""
        is_running, seconds = time_tracker.toggle_timer(task_list_with_tasks, 0)
        assert is_running is True
        assert seconds == 0
        assert time_tracker.active_task_index == 0

    def test_toggle_stops_timer(self, time_tracker, task_list_with_tasks):
        """Test toggle stops timer when running."""
        # Start timer
        time_tracker.start_timer(task_list_with_tasks, 0)
        import time
        time.sleep(0.1)

        # Toggle to stop
        is_running, seconds = time_tracker.toggle_timer(task_list_with_tasks, 0)
        assert is_running is False
        assert seconds >= 0
        assert time_tracker.active_task_index is None

    def test_toggle_switches_tasks(self, time_tracker, task_list_with_tasks):
        """Test toggle switches from one task to another."""
        # Start timer on task 0
        time_tracker.start_timer(task_list_with_tasks, 0)

        # Toggle task 1 (should stop task 0 and start task 1)
        is_running, seconds = time_tracker.toggle_timer(task_list_with_tasks, 1)
        assert is_running is True
        assert time_tracker.active_task_index == 1


class TestTimerPersistence:
    """Test timer state persistence (save/load)."""

    def test_save_state_creates_file(self, time_tracker, task_list_with_tasks, temp_state_file):
        """Test that starting timer saves state to file."""
        time_tracker.start_timer(task_list_with_tasks, 0)
        assert temp_state_file.exists()

    def test_load_state_restores_timer(self, temp_state_file, task_list_with_tasks):
        """Test that state is loaded from file on initialization."""
        # Create a tracker and start a timer
        tracker1 = TimeTracker(state_file=temp_state_file)
        tracker1.start_timer(task_list_with_tasks, 1)

        # Create a new tracker instance (should load state)
        tracker2 = TimeTracker(state_file=temp_state_file)
        assert tracker2.active_task_index == 1
        assert tracker2.active_task_date == task_list_with_tasks.date.isoformat()
        assert tracker2.timer_start_timestamp is not None

    def test_load_state_handles_corrupted_file(self, temp_state_file):
        """Test that corrupted state file doesn't crash the application."""
        # Write corrupted JSON
        temp_state_file.write_text("invalid json{{{")

        # Should not crash, should start with clean state
        tracker = TimeTracker(state_file=temp_state_file)
        assert tracker.active_task_index is None
        assert tracker.active_task_date is None

    def test_load_state_handles_missing_file(self, tmp_path):
        """Test loading state when file doesn't exist."""
        state_file = tmp_path / "nonexistent.json"
        tracker = TimeTracker(state_file=state_file)
        assert tracker.active_task_index is None

    def test_stop_timer_clears_state_file(self, time_tracker, task_list_with_tasks, temp_state_file):
        """Test that stopping timer updates state file."""
        time_tracker.start_timer(task_list_with_tasks, 0)
        time_tracker.stop_timer(task_list_with_tasks)

        # State should be cleared
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
        assert data['active_task_index'] is None
        assert data['active_task_date'] is None
        assert data['timer_start_timestamp'] is None


class TestManualTimeAdjustment:
    """Test manual time addition and subtraction."""

    def test_add_time_to_task(self, time_tracker):
        """Test manually adding time to a task."""
        task = Task("Test task", actual_seconds=100)
        time_tracker.add_manual_time(task, 50)
        assert task.actual_seconds == 150

    def test_subtract_time_from_task(self, time_tracker):
        """Test manually subtracting time from a task."""
        task = Task("Test task", actual_seconds=100)
        time_tracker.add_manual_time(task, -30)
        assert task.actual_seconds == 70

    def test_subtract_time_negative_clamps_to_zero(self, time_tracker):
        """Test that subtracting too much time clamps to zero."""
        task = Task("Test task", actual_seconds=50)
        time_tracker.add_manual_time(task, -100)
        assert task.actual_seconds == 0

    def test_add_negative_time(self, time_tracker):
        """Test adding negative time (same as subtraction)."""
        task = Task("Test task", actual_seconds=100)
        time_tracker.add_manual_time(task, -50)
        assert task.actual_seconds == 50


class TestElapsedTimeCalculation:
    """Test elapsed time calculations."""

    def test_get_elapsed_seconds_running_timer(self, time_tracker, task_list_with_tasks):
        """Test getting elapsed seconds for running timer."""
        time_tracker.start_timer(task_list_with_tasks, 0)
        import time
        time.sleep(0.1)

        task = task_list_with_tasks.tasks[0]
        elapsed = time_tracker.get_elapsed_seconds(task)
        assert elapsed >= 0

    def test_get_elapsed_seconds_no_timer(self, time_tracker):
        """Test getting elapsed seconds when timer is not running."""
        task = Task("Test task")
        elapsed = time_tracker.get_elapsed_seconds(task)
        assert elapsed == 0


class TestActiveTaskTracking:
    """Test active task tracking."""

    def test_is_timer_running_returns_true(self, time_tracker, task_list_with_tasks):
        """Test is_timer_running returns True for active task."""
        time_tracker.start_timer(task_list_with_tasks, 1)
        assert time_tracker.is_timer_running(1) is True

    def test_is_timer_running_returns_false(self, time_tracker, task_list_with_tasks):
        """Test is_timer_running returns False for inactive task."""
        time_tracker.start_timer(task_list_with_tasks, 1)
        assert time_tracker.is_timer_running(0) is False

    def test_is_timer_running_no_active_timer(self, time_tracker):
        """Test is_timer_running when no timer is active."""
        assert time_tracker.is_timer_running(0) is False


class TestClearTimer:
    """Test clear/cancel timer functionality."""

    def test_clear_timer_without_accumulating(self, time_tracker, task_list_with_tasks):
        """Test clearing timer doesn't accumulate time."""
        time_tracker.start_timer(task_list_with_tasks, 0)
        initial_actual = task_list_with_tasks.tasks[0].actual_seconds

        import time
        time.sleep(0.1)

        result = time_tracker.clear_timer(task_list_with_tasks)
        assert result is True
        assert task_list_with_tasks.tasks[0].actual_seconds == initial_actual
        assert time_tracker.active_task_index is None

    def test_clear_timer_when_no_timer(self, time_tracker, task_list_with_tasks):
        """Test clearing timer when none is running."""
        result = time_tracker.clear_timer(task_list_with_tasks)
        assert result is False


class TestAggregatedTime:
    """Test aggregated time for parent tasks."""

    def test_aggregated_time_single_task(self, time_tracker):
        """Test aggregated time for single task (no children)."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[Task("Single task", estimated_seconds=300, actual_seconds=200)]
        )
        estimated, actual = time_tracker.get_aggregated_time(task_list, 0)
        assert estimated == 300
        assert actual == 200

    def test_aggregated_time_with_children(self, time_tracker):
        """Test aggregated time sums parent and children."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Parent", indent_level=0, estimated_seconds=100, actual_seconds=50),
                Task("Child 1", indent_level=1, estimated_seconds=200, actual_seconds=100),
                Task("Child 2", indent_level=1, estimated_seconds=300, actual_seconds=150),
            ]
        )
        estimated, actual = time_tracker.get_aggregated_time(task_list, 0)
        assert estimated == 600  # 100 + 200 + 300
        assert actual == 300  # 50 + 100 + 150

    def test_aggregated_time_with_none_estimate(self, time_tracker):
        """Test aggregated time when some tasks have no estimate."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Parent", indent_level=0, estimated_seconds=100, actual_seconds=50),
                Task("Child 1", indent_level=1, estimated_seconds=None, actual_seconds=100),
            ]
        )
        estimated, actual = time_tracker.get_aggregated_time(task_list, 0)
        assert estimated is None
        assert actual == 150

    def test_aggregated_time_includes_running_timer(self, time_tracker):
        """Test aggregated time includes currently running timer."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Parent", indent_level=0, estimated_seconds=100, actual_seconds=50),
                Task("Child 1", indent_level=1, estimated_seconds=200, actual_seconds=100),
            ]
        )

        # Start timer on child
        time_tracker.start_timer(task_list, 1)
        import time
        time.sleep(0.2)  # Sleep a bit longer to ensure measurable time

        estimated, actual = time_tracker.get_aggregated_time(task_list, 0)
        assert estimated == 300
        assert actual >= 150  # Should be at least the base amount (allow for timing imprecision)


class TestTimerSync:
    """Test timer synchronization with task lists."""

    def test_sync_restores_timer_start(self, time_tracker, task_list_with_tasks):
        """Test sync restores timer_start on correct task."""
        # Start timer
        time_tracker.start_timer(task_list_with_tasks, 1)
        original_timestamp = time_tracker.timer_start_timestamp

        # Create new task list (simulating reload)
        new_task_list = DailyTaskList(
            date=task_list_with_tasks.date,
            tasks=[
                Task("Task 1"),
                Task("Task 2"),
                Task("Task 3"),
            ]
        )

        # Sync should restore timer_start
        time_tracker.sync_timer_with_task_list(new_task_list)
        assert new_task_list.tasks[1].timer_start is not None

    def test_sync_ignores_different_date(self, time_tracker, task_list_with_tasks):
        """Test sync doesn't restore timer for different date."""
        # Start timer
        time_tracker.start_timer(task_list_with_tasks, 1)

        # Create task list for different date
        different_date_list = DailyTaskList(
            date=date.today() - timedelta(days=1),
            tasks=[Task("Task 1"), Task("Task 2")]
        )

        # Sync should not restore timer
        time_tracker.sync_timer_with_task_list(different_date_list)
        assert different_date_list.tasks[1].timer_start is None

    def test_sync_clears_invalid_index(self, temp_state_file):
        """Test sync clears timer state if task index is invalid."""
        # Manually create invalid state
        state = {
            'active_task_index': 5,  # Invalid index
            'active_task_date': date.today().isoformat(),
            'timer_start_timestamp': datetime.now().isoformat()
        }
        with open(temp_state_file, 'w') as f:
            json.dump(state, f)

        tracker = TimeTracker(state_file=temp_state_file)
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[Task("Task 1"), Task("Task 2")]
        )

        tracker.sync_timer_with_task_list(task_list)
        assert tracker.active_task_index is None

    def test_sync_handles_invalid_timestamp(self, temp_state_file):
        """Test sync handles invalid timestamp gracefully."""
        # Manually create state with invalid timestamp
        state = {
            'active_task_index': 0,
            'active_task_date': date.today().isoformat(),
            'timer_start_timestamp': 'invalid-timestamp'
        }
        with open(temp_state_file, 'w') as f:
            json.dump(state, f)

        tracker = TimeTracker(state_file=temp_state_file)
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[Task("Task 1")]
        )

        tracker.sync_timer_with_task_list(task_list)
        assert tracker.active_task_index is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_stop_timer_with_invalid_index(self, time_tracker, task_list_with_tasks):
        """Test stopping timer when active index is now invalid."""
        time_tracker.start_timer(task_list_with_tasks, 0)

        # Manually set invalid index
        time_tracker.active_task_index = 99

        result = time_tracker.stop_timer(task_list_with_tasks)
        assert result == 0
        assert time_tracker.active_task_index is None

    def test_stop_timer_with_no_timer_start(self, time_tracker, task_list_with_tasks):
        """Test stopping timer when task has no timer_start."""
        time_tracker.active_task_index = 0
        # Don't actually start timer, just set the index

        result = time_tracker.stop_timer(task_list_with_tasks)
        assert result == 0
        assert time_tracker.active_task_index is None

    def test_concurrent_timers_not_possible(self, time_tracker, task_list_with_tasks):
        """Test that only one timer can run at a time."""
        time_tracker.start_timer(task_list_with_tasks, 0)
        time_tracker.start_timer(task_list_with_tasks, 1)

        # Only task 1 should have timer running
        assert task_list_with_tasks.tasks[0].timer_start is None
        assert task_list_with_tasks.tasks[1].timer_start is not None
        assert time_tracker.active_task_index == 1

    def test_empty_task_list(self, time_tracker):
        """Test operations on empty task list."""
        empty_list = DailyTaskList(date=date.today(), tasks=[])
        result = time_tracker.start_timer(empty_list, 0)
        assert result is False

    def test_save_state_io_error(self, tmp_path):
        """Test that IO errors during save don't crash the app."""
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        state_file = readonly_dir / "timer_state.json"

        tracker = TimeTracker(state_file=state_file)

        # Make directory read-only (on Unix-like systems)
        import os
        if os.name != 'nt':  # Skip on Windows
            readonly_dir.chmod(0o444)

            task_list = DailyTaskList(date=date.today(), tasks=[Task("Test")])
            # Should not crash even if save fails
            tracker.start_timer(task_list, 0)

            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)
