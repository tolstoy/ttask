"""Scoring system for time tracking with efficiency multiplier.

This module provides a gamified scoring system that encourages accurate task
estimation and efficient execution. The scoring formula incentivizes both
beating estimates and making ambitious (short) estimates.

Scoring Formula:
    points = (estimate_minutes - actual_minutes) * efficiency_multiplier
    where efficiency_multiplier = 100 / (estimate_minutes + 10)

Examples:
    - Beat a 10-minute task by 5 min: 5 * (100/20) = 25 points
    - Beat a 60-minute task by 5 min: 5 * (100/70) = 7.14 points

This incentivizes making realistic estimates (too-short estimates are penalized
by the multiplier if you don't beat them).
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict
from pathlib import Path
import json
from models import Task, DailyTaskList


@dataclass
class DailyScore:
    """Statistics and score for a single day.

    Tracks both point-based score and efficiency metrics for a day's tasks.

    Attributes:
        date: The date these statistics are for
        total_score: Total points earned (can be negative if over estimates)
        tasks_completed: Number of completed tasks (regardless of estimate)
        tasks_beat_estimate: Number of tasks where actual <= estimated time
        tasks_over_estimate: Number of tasks where actual > estimated time
        total_estimated_minutes: Sum of all task estimates (in minutes)
        total_actual_minutes: Sum of all actual time spent (in minutes)
        efficiency_ratio: Ratio of actual/estimated (lower is better, 1.0 is perfect)
    """
    date: date
    total_score: float
    tasks_completed: int
    tasks_beat_estimate: int
    tasks_over_estimate: int
    total_estimated_minutes: int
    total_actual_minutes: int
    efficiency_ratio: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'date': self.date.isoformat(),
            'total_score': self.total_score,
            'tasks_completed': self.tasks_completed,
            'tasks_beat_estimate': self.tasks_beat_estimate,
            'tasks_over_estimate': self.tasks_over_estimate,
            'total_estimated_minutes': self.total_estimated_minutes,
            'total_actual_minutes': self.total_actual_minutes,
            'efficiency_ratio': self.efficiency_ratio,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DailyScore':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            date=date.fromisoformat(data['date']),
            total_score=data['total_score'],
            tasks_completed=data['tasks_completed'],
            tasks_beat_estimate=data['tasks_beat_estimate'],
            tasks_over_estimate=data['tasks_over_estimate'],
            total_estimated_minutes=data['total_estimated_minutes'],
            total_actual_minutes=data['total_actual_minutes'],
            efficiency_ratio=data['efficiency_ratio'],
        )


class ScoringSystem:
    """
    Calculate scores for tasks with efficiency multiplier.

    Scoring Formula:
    - points = (estimate - actual) * efficiency_multiplier
    - efficiency_multiplier = 100 / (estimate_minutes + 10)

    This incentivizes:
    - Lower estimates (higher multiplier)
    - Beating estimates (positive delta)
    - Example: Beat 10m by 5m = 5 * 5.0 = 25pts
    - Example: Beat 60m by 5m = 5 * 1.43 = 7pts
    """

    def __init__(self, stats_file: Optional[Path] = None):
        """
        Initialize scoring system.

        Args:
            stats_file: Path to file for persisting statistics. If None, uses default.
        """
        if stats_file is None:
            self.stats_file = Path.home() / ".taskjournal" / "stats.json"
        else:
            self.stats_file = stats_file

        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.daily_scores: Dict[str, DailyScore] = {}
        self._load_stats()

    def _load_stats(self):
        """Load statistics from file if it exists."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.daily_scores = {
                        date_str: DailyScore.from_dict(score_data)
                        for date_str, score_data in data.get('daily_scores', {}).items()
                    }
            except (json.JSONDecodeError, IOError, KeyError):
                # If file is corrupted, start fresh
                self.daily_scores = {}

    def _save_stats(self):
        """Save statistics to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump({
                    'daily_scores': {
                        date_str: score.to_dict()
                        for date_str, score in self.daily_scores.items()
                    }
                }, f, indent=2)
        except IOError:
            # If we can't save stats, continue without persistence
            pass

    @staticmethod
    def calculate_efficiency_multiplier(estimated_seconds: int) -> float:
        """
        Calculate efficiency multiplier based on estimate.

        Lower estimates get higher multipliers, incentivizing ambitious goals
        while penalizing overly-ambitious (unbeatable) estimates.

        Formula: 100 / (estimated_minutes + 10)

        Args:
            estimated_seconds: The estimated time in seconds

        Returns:
            Efficiency multiplier (higher for lower estimates)

        Example:
            >>> ScoringSystem.calculate_efficiency_multiplier(600)  # 10 min = (100 / 20) = 5.0
            5.0
            >>> ScoringSystem.calculate_efficiency_multiplier(3600)  # 60 min = (100 / 70) = 1.43
            1.4285714285714286
        """
        # Convert to minutes for the formula (keeps scores similar to before)
        estimated_minutes = estimated_seconds / 60.0
        return 100.0 / (estimated_minutes + 10)

    @staticmethod
    def calculate_task_score(task: Task) -> float:
        """
        Calculate score for a single task.

        Only scores completed tasks with estimates. Returns 0 for incomplete
        tasks or tasks without estimates.

        Args:
            task: The task to score (must be completed and have estimated_seconds)

        Returns:
            Score (positive if beat estimate, negative if over, 0 if no estimate)

        Example:
            >>> task = Task("Work", completed=True, estimated_seconds=600, actual_seconds=300)
            >>> ScoringSystem.calculate_task_score(task)  # Beat 10m by 5m = 5 * 5.0 = 25.0
            25.0
        """
        if task.estimated_seconds is None:
            return 0.0

        if not task.completed:
            return 0.0

        # Work in minutes for the scoring formula
        estimated_minutes = task.estimated_seconds / 60.0
        actual_minutes = task.actual_seconds / 60.0

        delta = estimated_minutes - actual_minutes
        multiplier = ScoringSystem.calculate_efficiency_multiplier(task.estimated_seconds)
        return delta * multiplier

    def calculate_daily_score(self, task_list: DailyTaskList) -> DailyScore:
        """
        Calculate comprehensive daily score and statistics.

        Analyzes all tasks in the daily list, calculates points based on the
        scoring formula, and tracks efficiency metrics. Results are persisted
        to the stats file.

        Args:
            task_list: The daily task list to score

        Returns:
            DailyScore object with all statistics (also persisted)

        Note:
            Results are automatically saved to stats_file for streak and
            historical analysis.
        """
        total_score = 0.0
        tasks_completed = 0
        tasks_beat_estimate = 0
        tasks_over_estimate = 0
        total_estimated_minutes = 0
        total_actual_minutes = 0

        for task in task_list.tasks:
            if task.completed:
                tasks_completed += 1

                if task.estimated_seconds is not None:
                    score = self.calculate_task_score(task)
                    total_score += score

                    # Store in minutes for backward compatibility with display
                    total_estimated_minutes += int(task.estimated_seconds / 60)
                    total_actual_minutes += int(task.actual_seconds / 60)

                    if task.actual_seconds <= task.estimated_seconds:
                        tasks_beat_estimate += 1
                    else:
                        tasks_over_estimate += 1

        # Calculate efficiency ratio (actual/estimated)
        if total_estimated_minutes > 0:
            efficiency_ratio = total_actual_minutes / total_estimated_minutes
        else:
            efficiency_ratio = 1.0

        daily_score = DailyScore(
            date=task_list.date,
            total_score=total_score,
            tasks_completed=tasks_completed,
            tasks_beat_estimate=tasks_beat_estimate,
            tasks_over_estimate=tasks_over_estimate,
            total_estimated_minutes=total_estimated_minutes,
            total_actual_minutes=total_actual_minutes,
            efficiency_ratio=efficiency_ratio,
        )

        # Save to history
        date_str = task_list.date.isoformat()
        self.daily_scores[date_str] = daily_score
        self._save_stats()

        return daily_score

    def get_streak(self, current_date: date) -> int:
        """
        Calculate current streak of days with positive scores.

        Counts backwards from the given date to find the longest sequence
        of consecutive days with positive scores (total_score > 0).

        Args:
            current_date: The current date to calculate streak from (search goes backwards)

        Returns:
            Number of consecutive days with positive scores (0 if current day has no positive score)

        Example:
            >>> scoring = ScoringSystem()
            >>> # If Nov 9, 8, 7 all have positive scores but Nov 6 doesn't:
            >>> scoring.get_streak(date(2025, 11, 9))  # Returns 3
        """
        streak = 0
        check_date = current_date

        while True:
            date_str = check_date.isoformat()
            if date_str not in self.daily_scores:
                break

            daily_score = self.daily_scores[date_str]
            if daily_score.total_score <= 0:
                break

            streak += 1
            # Move to previous day
            from datetime import timedelta
            check_date = check_date - timedelta(days=1)

        return streak

    def get_daily_score(self, task_date: date) -> Optional[DailyScore]:
        """
        Get the score for a specific date.

        Retrieves previously calculated score from the loaded stats file.

        Args:
            task_date: The date to get score for

        Returns:
            DailyScore if exists, None if no score has been calculated for that date
        """
        date_str = task_date.isoformat()
        return self.daily_scores.get(date_str)

    def get_average_efficiency(self, days: int = 7) -> float:
        """
        Get average efficiency ratio over the last N days.

        Calculates the mean efficiency_ratio (actual/estimated time) over the
        most recent N days with scores. Lower is better (1.0 = perfect estimates).

        Args:
            days: Number of recent days to average over (default: 7)

        Returns:
            Average efficiency ratio (actual/estimated). Returns 1.0 if no scores exist.

        Example:
            >>> scoring = ScoringSystem()
            >>> efficiency = scoring.get_average_efficiency(days=7)
            >>> # 0.9 means on average taking 90% of estimated time (beating estimates)
            >>> # 1.1 means on average taking 110% of estimated time (missing estimates)
        """
        if not self.daily_scores:
            return 1.0

        # Get the most recent scores
        sorted_scores = sorted(
            self.daily_scores.values(),
            key=lambda s: s.date,
            reverse=True
        )[:days]

        if not sorted_scores:
            return 1.0

        total_efficiency = sum(s.efficiency_ratio for s in sorted_scores)
        return total_efficiency / len(sorted_scores)
