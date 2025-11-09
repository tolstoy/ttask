"""Scoring system for time tracking with efficiency multiplier."""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict
from pathlib import Path
import json
from models import Task, DailyTaskList


@dataclass
class DailyScore:
    """Statistics and score for a single day."""
    date: date
    total_score: float
    tasks_completed: int
    tasks_beat_estimate: int
    tasks_over_estimate: int
    total_estimated_minutes: int
    total_actual_minutes: int
    efficiency_ratio: float  # actual/estimated (lower is better)

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

        Lower estimates get higher multipliers, incentivizing ambitious goals.

        Args:
            estimated_seconds: The estimated time in seconds

        Returns:
            Efficiency multiplier (higher for lower estimates)
        """
        # Convert to minutes for the formula (keeps scores similar to before)
        estimated_minutes = estimated_seconds / 60.0
        return 100.0 / (estimated_minutes + 10)

    @staticmethod
    def calculate_task_score(task: Task) -> float:
        """
        Calculate score for a single task.

        Args:
            task: The task to score

        Returns:
            Score (positive if beat estimate, negative if over)
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

        Args:
            task_list: The daily task list

        Returns:
            DailyScore object with all statistics
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

        Args:
            current_date: The current date to calculate streak from

        Returns:
            Number of consecutive days with positive scores
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

        Args:
            task_date: The date to get score for

        Returns:
            DailyScore if exists, None otherwise
        """
        date_str = task_date.isoformat()
        return self.daily_scores.get(date_str)

    def get_average_efficiency(self, days: int = 7) -> float:
        """
        Get average efficiency ratio over the last N days.

        Args:
            days: Number of days to average over

        Returns:
            Average efficiency ratio (actual/estimated)
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
