"""Time tracking functionality for tasks."""
from datetime import datetime, timedelta
from typing import Optional, List
from models import Task, DailyTaskList
from pathlib import Path
import json


class TimeTracker:
    """
    Handles time tracking for tasks with both active timer and manual entry.

    Features:
    - Start/stop timer for active task tracking
    - Manual time addition/subtraction
    - Persistent timer state across app restarts
    - Parent-child time aggregation
    """

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize TimeTracker.

        Args:
            state_file: Path to file for persisting timer state. If None, uses default.
        """
        if state_file is None:
            self.state_file = Path.home() / ".taskjournal" / "timer_state.json"
        else:
            self.state_file = state_file

        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.active_task_index: Optional[int] = None
        self.active_task_date: Optional[str] = None  # ISO format date string
        self.timer_start_timestamp: Optional[str] = None  # ISO format datetime string
        self._load_state()

    def _load_state(self):
        """Load timer state from file if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.active_task_index = data.get('active_task_index')
                    self.active_task_date = data.get('active_task_date')
                    self.timer_start_timestamp = data.get('timer_start_timestamp')
            except (json.JSONDecodeError, IOError):
                # If file is corrupted or unreadable, start fresh
                self.active_task_index = None
                self.active_task_date = None
                self.timer_start_timestamp = None

    def _save_state(self):
        """Save timer state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'active_task_index': self.active_task_index,
                    'active_task_date': self.active_task_date,
                    'timer_start_timestamp': self.timer_start_timestamp
                }, f)
        except IOError:
            # If we can't save state, continue without persistence
            pass

    def start_timer(self, task_list: DailyTaskList, task_index: int) -> bool:
        """
        Start timer for a task. Stops any currently running timer first.

        Args:
            task_list: The daily task list
            task_index: Index of task to start timing

        Returns:
            True if timer started, False if invalid index
        """
        if not (0 <= task_index < len(task_list.tasks)):
            return False

        # Stop currently running timer if any
        if self.active_task_index is not None:
            self.stop_timer(task_list)

        # Start new timer
        task = task_list.tasks[task_index]
        now = datetime.now()
        task.timer_start = now
        self.active_task_index = task_index
        self.active_task_date = task_list.date.isoformat()
        self.timer_start_timestamp = now.isoformat()
        self._save_state()
        return True

    def stop_timer(self, task_list: DailyTaskList) -> int:
        """
        Stop the currently running timer and accumulate time.

        Args:
            task_list: The daily task list

        Returns:
            Number of seconds that were accumulated (0 if no timer running)
        """
        if self.active_task_index is None:
            return 0

        if not (0 <= self.active_task_index < len(task_list.tasks)):
            self.active_task_index = None
            self._save_state()
            return 0

        task = task_list.tasks[self.active_task_index]
        if task.timer_start is None:
            self.active_task_index = None
            self._save_state()
            return 0

        # Calculate elapsed time in seconds
        elapsed = datetime.now() - task.timer_start
        seconds = int(elapsed.total_seconds())

        # Accumulate the seconds
        task.actual_seconds += seconds

        task.timer_start = None
        self.active_task_index = None
        self.active_task_date = None
        self.timer_start_timestamp = None
        self._save_state()

        return seconds

    def toggle_timer(self, task_list: DailyTaskList, task_index: int) -> tuple[bool, int]:
        """
        Toggle timer for a task (start if stopped, stop if running).

        Args:
            task_list: The daily task list
            task_index: Index of task to toggle

        Returns:
            Tuple of (is_now_running, seconds_accumulated)
            - is_now_running: True if timer is now running, False if stopped
            - seconds_accumulated: Seconds added when stopping (0 if starting)
        """
        # If this task has the active timer, stop it
        if self.active_task_index == task_index:
            seconds = self.stop_timer(task_list)
            return False, seconds

        # Otherwise start timer on this task (stops any other timer)
        self.start_timer(task_list, task_index)
        return True, 0

    def get_elapsed_seconds(self, task: Task) -> int:
        """
        Get currently elapsed seconds for a task with active timer.

        Args:
            task: The task to check

        Returns:
            Number of seconds elapsed (0 if timer not running)
        """
        if task.timer_start is None:
            return 0

        elapsed = datetime.now() - task.timer_start
        return int(elapsed.total_seconds())

    def clear_timer(self, task_list: DailyTaskList) -> bool:
        """
        Clear/cancel the currently running timer without adding time.

        Args:
            task_list: The daily task list

        Returns:
            True if a timer was cleared, False if no timer was running
        """
        if self.active_task_index is None:
            return False

        if not (0 <= self.active_task_index < len(task_list.tasks)):
            self.active_task_index = None
            self._save_state()
            return False

        task = task_list.tasks[self.active_task_index]
        if task.timer_start is None:
            self.active_task_index = None
            self._save_state()
            return False

        # Clear timer without accumulating time
        task.timer_start = None
        self.active_task_index = None
        self.active_task_date = None
        self.timer_start_timestamp = None
        self._save_state()

        return True

    def add_manual_time(self, task: Task, seconds: int):
        """
        Manually add time to a task.

        Args:
            task: The task to add time to
            seconds: Number of seconds to add (can be negative to subtract)
        """
        task.actual_seconds = max(0, task.actual_seconds + seconds)

    def get_aggregated_time(self, task_list: DailyTaskList, parent_index: int) -> tuple[Optional[int], int]:
        """
        Get aggregated time for a parent task and all its children.

        Args:
            task_list: The daily task list
            parent_index: Index of the parent task

        Returns:
            Tuple of (total_estimated_seconds, total_actual_seconds)
            - total_estimated_seconds: Sum of estimates in seconds (None if any child has no estimate)
            - total_actual_seconds: Sum of actual time spent in seconds
        """
        from business_logic.task_operations import get_task_group

        start, end = get_task_group(task_list.tasks, parent_index)
        tasks_in_group = task_list.tasks[start:end + 1]

        # If this is a leaf task (no children), return its own times
        if len(tasks_in_group) == 1:
            task = tasks_in_group[0]
            return task.estimated_seconds, task.actual_seconds

        # Sum up times from all tasks in the group
        total_estimated = 0
        has_all_estimates = True
        total_actual = 0

        for task in tasks_in_group:
            if task.estimated_seconds is None:
                has_all_estimates = False
            else:
                total_estimated += task.estimated_seconds

            total_actual += task.actual_seconds

            # Add currently running timer time
            if task.timer_start is not None:
                total_actual += self.get_elapsed_seconds(task)

        return (total_estimated if has_all_estimates else None), total_actual

    def is_timer_running(self, task_index: int) -> bool:
        """
        Check if a specific task has an active timer.

        Args:
            task_index: Index of task to check

        Returns:
            True if this task has the active timer
        """
        return self.active_task_index == task_index

    def sync_timer_with_task_list(self, task_list: DailyTaskList):
        """
        Sync timer state with a loaded task list.

        If the loaded day matches the active timer's date, restore the timer_start
        on the appropriate task so the timer continues running with correct elapsed time.

        Args:
            task_list: The daily task list that was just loaded
        """
        # No active timer, nothing to sync
        if self.active_task_index is None or self.active_task_date is None or self.timer_start_timestamp is None:
            return

        # Check if this is the day with the active timer
        if task_list.date.isoformat() != self.active_task_date:
            # Timer is running on a different day, don't modify this day's tasks
            return

        # Verify the task index is valid
        if not (0 <= self.active_task_index < len(task_list.tasks)):
            # Task index is out of bounds (maybe task was deleted), clear timer state
            self.active_task_index = None
            self.active_task_date = None
            self.timer_start_timestamp = None
            self._save_state()
            return

        # Restore timer_start on the task
        try:
            timer_start = datetime.fromisoformat(self.timer_start_timestamp)
            task_list.tasks[self.active_task_index].timer_start = timer_start
        except (ValueError, AttributeError):
            # Invalid timestamp, clear timer state
            self.active_task_index = None
            self.active_task_date = None
            self.timer_start_timestamp = None
            self._save_state()
