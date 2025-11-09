"""Tests for scoring system functionality."""
import pytest
from datetime import date, timedelta
from pathlib import Path
import json
import tempfile
from models import Task, DailyTaskList
from business_logic.scoring import ScoringSystem, DailyScore


@pytest.fixture
def temp_stats_file():
    """Create a temporary file for statistics."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def scoring_system(temp_stats_file):
    """Create a ScoringSystem instance with temporary stats file."""
    return ScoringSystem(stats_file=temp_stats_file)


@pytest.fixture
def completed_tasks_list():
    """Create a DailyTaskList with completed tasks."""
    return DailyTaskList(
        date=date.today(),
        tasks=[
            # Beat estimate by 2 minutes
            Task("Fast task", completed=True, estimated_seconds=300, actual_seconds=180),
            # Matched estimate exactly
            Task("On time task", completed=True, estimated_seconds=600, actual_seconds=600),
            # Over estimate by 5 minutes
            Task("Slow task", completed=True, estimated_seconds=300, actual_seconds=600),
            # Completed but no estimate
            Task("No estimate", completed=True, estimated_seconds=None, actual_seconds=100),
            # Incomplete task (should not count)
            Task("Incomplete", completed=False, estimated_seconds=300, actual_seconds=50),
        ]
    )


class TestScoringSystemInitialization:
    """Test ScoringSystem initialization."""

    def test_init_creates_default_stats_file(self):
        """Test that initialization creates default stats file path."""
        scorer = ScoringSystem()
        assert scorer.stats_file == Path.home() / ".taskjournal" / "stats.json"
        assert isinstance(scorer.daily_scores, dict)  # May have existing data

    def test_init_with_custom_stats_file(self, temp_stats_file):
        """Test initialization with custom stats file."""
        scorer = ScoringSystem(stats_file=temp_stats_file)
        assert scorer.stats_file == temp_stats_file

    def test_init_creates_parent_directory(self, tmp_path):
        """Test that initialization creates parent directory if needed."""
        stats_file = tmp_path / "subdir" / "stats.json"
        scorer = ScoringSystem(stats_file=stats_file)
        assert stats_file.parent.exists()


class TestEfficiencyMultiplier:
    """Test efficiency multiplier calculation."""

    def test_low_estimate_high_multiplier(self):
        """Test that lower estimates get higher multipliers."""
        # 5 minutes = 300 seconds
        multiplier_5m = ScoringSystem.calculate_efficiency_multiplier(300)
        # 60 minutes = 3600 seconds
        multiplier_60m = ScoringSystem.calculate_efficiency_multiplier(3600)

        # Lower estimate should have higher multiplier
        assert multiplier_5m > multiplier_60m

    def test_multiplier_formula(self):
        """Test multiplier calculation formula."""
        # 10 minutes = 600 seconds
        # Formula: 100 / (10 + 10) = 5.0
        multiplier = ScoringSystem.calculate_efficiency_multiplier(600)
        assert abs(multiplier - 5.0) < 0.01

    def test_multiplier_for_very_short_task(self):
        """Test multiplier for very short tasks."""
        # 1 minute = 60 seconds
        # Formula: 100 / (1 + 10) = 9.09
        multiplier = ScoringSystem.calculate_efficiency_multiplier(60)
        assert abs(multiplier - 9.09) < 0.01

    def test_multiplier_for_very_long_task(self):
        """Test multiplier for very long tasks."""
        # 120 minutes = 7200 seconds
        # Formula: 100 / (120 + 10) = 0.769
        multiplier = ScoringSystem.calculate_efficiency_multiplier(7200)
        assert abs(multiplier - 0.769) < 0.01


class TestTaskScoreCalculation:
    """Test individual task score calculation."""

    def test_score_beat_estimate(self):
        """Test positive score when beating estimate."""
        task = Task(
            "Fast task",
            completed=True,
            estimated_seconds=600,  # 10 minutes
            actual_seconds=300  # 5 minutes
        )
        score = ScoringSystem.calculate_task_score(task)
        # Beat by 5 minutes, multiplier = 100/(10+10) = 5.0
        # Score = 5 * 5.0 = 25.0
        assert abs(score - 25.0) < 0.1

    def test_score_over_estimate(self):
        """Test negative score when over estimate."""
        task = Task(
            "Slow task",
            completed=True,
            estimated_seconds=600,  # 10 minutes
            actual_seconds=900  # 15 minutes
        )
        score = ScoringSystem.calculate_task_score(task)
        # Over by 5 minutes, multiplier = 5.0
        # Score = -5 * 5.0 = -25.0
        assert abs(score - (-25.0)) < 0.1

    def test_score_match_estimate(self):
        """Test zero score when matching estimate exactly."""
        task = Task(
            "On time task",
            completed=True,
            estimated_seconds=600,
            actual_seconds=600
        )
        score = ScoringSystem.calculate_task_score(task)
        assert abs(score) < 0.1

    def test_score_incomplete_task(self):
        """Test that incomplete tasks score zero."""
        task = Task(
            "Incomplete",
            completed=False,
            estimated_seconds=600,
            actual_seconds=300
        )
        score = ScoringSystem.calculate_task_score(task)
        assert score == 0.0

    def test_score_no_estimate(self):
        """Test that tasks without estimate score zero."""
        task = Task(
            "No estimate",
            completed=True,
            estimated_seconds=None,
            actual_seconds=300
        )
        score = ScoringSystem.calculate_task_score(task)
        assert score == 0.0

    def test_score_zero_actual_time(self):
        """Test scoring task with zero actual time."""
        task = Task(
            "Instant task",
            completed=True,
            estimated_seconds=600,  # 10 minutes
            actual_seconds=0
        )
        score = ScoringSystem.calculate_task_score(task)
        # Beat by 10 minutes, multiplier = 5.0
        # Score = 10 * 5.0 = 50.0
        assert abs(score - 50.0) < 0.1


class TestDailyScoreCalculation:
    """Test daily score and statistics calculation."""

    def test_calculate_daily_score_basic(self, scoring_system, completed_tasks_list):
        """Test basic daily score calculation."""
        daily_score = scoring_system.calculate_daily_score(completed_tasks_list)

        assert daily_score.date == completed_tasks_list.date
        assert daily_score.tasks_completed == 4  # 4 completed tasks
        assert isinstance(daily_score.total_score, float)

    def test_calculate_daily_score_counts_beat_vs_over(self, scoring_system, completed_tasks_list):
        """Test counting tasks that beat vs exceeded estimates."""
        daily_score = scoring_system.calculate_daily_score(completed_tasks_list)

        # From fixture: 1 beat (180/300), 1 matched (600/600), 1 over (600/300), 1 no estimate
        assert daily_score.tasks_beat_estimate == 2  # Beat and matched both count
        assert daily_score.tasks_over_estimate == 1

    def test_calculate_daily_score_time_totals(self, scoring_system, completed_tasks_list):
        """Test time totals in daily score."""
        daily_score = scoring_system.calculate_daily_score(completed_tasks_list)

        # Tasks with estimates: 300 + 600 + 300 = 1200 seconds = 20 minutes
        assert daily_score.total_estimated_minutes == 20
        # Actual: 180 + 600 + 600 = 1380 seconds = 23 minutes
        assert daily_score.total_actual_minutes == 23

    def test_calculate_daily_score_efficiency_ratio(self, scoring_system, completed_tasks_list):
        """Test efficiency ratio calculation."""
        daily_score = scoring_system.calculate_daily_score(completed_tasks_list)

        # actual / estimated = 23 / 20 = 1.15
        assert abs(daily_score.efficiency_ratio - 1.15) < 0.01

    def test_calculate_daily_score_empty_list(self, scoring_system):
        """Test daily score for empty task list."""
        empty_list = DailyTaskList(date=date.today(), tasks=[])
        daily_score = scoring_system.calculate_daily_score(empty_list)

        assert daily_score.tasks_completed == 0
        assert daily_score.total_score == 0.0
        assert daily_score.efficiency_ratio == 1.0

    def test_calculate_daily_score_no_estimates(self, scoring_system):
        """Test daily score when no tasks have estimates."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task 1", completed=True, estimated_seconds=None, actual_seconds=100),
                Task("Task 2", completed=True, estimated_seconds=None, actual_seconds=200),
            ]
        )
        daily_score = scoring_system.calculate_daily_score(task_list)

        assert daily_score.tasks_completed == 2
        assert daily_score.total_score == 0.0
        assert daily_score.total_estimated_minutes == 0
        assert daily_score.efficiency_ratio == 1.0


class TestScorePersistence:
    """Test score saving and loading."""

    def test_save_score_creates_file(self, scoring_system, completed_tasks_list, temp_stats_file):
        """Test that calculating score saves to file."""
        scoring_system.calculate_daily_score(completed_tasks_list)
        assert temp_stats_file.exists()

    def test_save_and_load_score(self, temp_stats_file, completed_tasks_list):
        """Test that scores are saved and loaded correctly."""
        # Create scorer and calculate score
        scorer1 = ScoringSystem(stats_file=temp_stats_file)
        daily_score = scorer1.calculate_daily_score(completed_tasks_list)

        # Create new scorer instance (should load from file)
        scorer2 = ScoringSystem(stats_file=temp_stats_file)
        date_str = completed_tasks_list.date.isoformat()
        loaded_score = scorer2.daily_scores[date_str]

        assert loaded_score.date == daily_score.date
        assert loaded_score.total_score == daily_score.total_score
        assert loaded_score.tasks_completed == daily_score.tasks_completed

    def test_load_corrupted_stats_file(self, temp_stats_file):
        """Test that corrupted stats file doesn't crash the application."""
        # Write corrupted JSON
        temp_stats_file.write_text("invalid json{{{")

        # Should not crash, should start with empty scores
        scorer = ScoringSystem(stats_file=temp_stats_file)
        assert scorer.daily_scores == {}

    def test_load_missing_file(self, tmp_path):
        """Test loading when file doesn't exist."""
        stats_file = tmp_path / "nonexistent.json"
        scorer = ScoringSystem(stats_file=stats_file)
        assert scorer.daily_scores == {}

    def test_multiple_days_persistence(self, temp_stats_file):
        """Test saving scores for multiple days."""
        scorer = ScoringSystem(stats_file=temp_stats_file)

        # Add scores for 3 different days
        for i in range(3):
            task_list = DailyTaskList(
                date=date.today() - timedelta(days=i),
                tasks=[
                    Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
                ]
            )
            scorer.calculate_daily_score(task_list)

        # Reload and verify
        scorer2 = ScoringSystem(stats_file=temp_stats_file)
        assert len(scorer2.daily_scores) == 3


class TestDailyScoreDataClass:
    """Test DailyScore dataclass serialization."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        score = DailyScore(
            date=date(2025, 1, 15),
            total_score=42.5,
            tasks_completed=5,
            tasks_beat_estimate=3,
            tasks_over_estimate=2,
            total_estimated_minutes=60,
            total_actual_minutes=55,
            efficiency_ratio=0.92
        )
        data = score.to_dict()

        assert data['date'] == '2025-01-15'
        assert data['total_score'] == 42.5
        assert data['tasks_completed'] == 5

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'date': '2025-01-15',
            'total_score': 42.5,
            'tasks_completed': 5,
            'tasks_beat_estimate': 3,
            'tasks_over_estimate': 2,
            'total_estimated_minutes': 60,
            'total_actual_minutes': 55,
            'efficiency_ratio': 0.92
        }
        score = DailyScore.from_dict(data)

        assert score.date == date(2025, 1, 15)
        assert score.total_score == 42.5
        assert score.tasks_completed == 5

    def test_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = DailyScore(
            date=date(2025, 1, 15),
            total_score=42.5,
            tasks_completed=5,
            tasks_beat_estimate=3,
            tasks_over_estimate=2,
            total_estimated_minutes=60,
            total_actual_minutes=55,
            efficiency_ratio=0.92
        )
        data = original.to_dict()
        restored = DailyScore.from_dict(data)

        assert restored.date == original.date
        assert restored.total_score == original.total_score
        assert restored.efficiency_ratio == original.efficiency_ratio


class TestStreakCalculation:
    """Test streak calculation."""

    def test_streak_single_day(self, scoring_system):
        """Test streak with single positive day."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        streak = scoring_system.get_streak(date.today())
        assert streak == 1

    def test_streak_multiple_days(self, scoring_system):
        """Test streak across multiple consecutive days."""
        # Add positive scores for 5 consecutive days
        for i in range(5):
            task_list = DailyTaskList(
                date=date.today() - timedelta(days=i),
                tasks=[
                    Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
                ]
            )
            scoring_system.calculate_daily_score(task_list)

        streak = scoring_system.get_streak(date.today())
        assert streak == 5

    def test_streak_breaks_on_negative_score(self, scoring_system):
        """Test that streak breaks on negative score."""
        # Day 0: positive
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        # Day 1: negative (over estimate significantly)
        task_list = DailyTaskList(
            date=date.today() - timedelta(days=1),
            tasks=[
                Task("Task", completed=True, estimated_seconds=300, actual_seconds=900)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        # Day 2: positive
        task_list = DailyTaskList(
            date=date.today() - timedelta(days=2),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        streak = scoring_system.get_streak(date.today())
        assert streak == 1  # Only day 0

    def test_streak_breaks_on_missing_day(self, scoring_system):
        """Test that streak breaks on missing day."""
        # Day 0: positive
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        # Skip day 1

        # Day 2: positive
        task_list = DailyTaskList(
            date=date.today() - timedelta(days=2),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        streak = scoring_system.get_streak(date.today())
        assert streak == 1  # Only day 0

    def test_streak_zero_on_no_data(self, scoring_system):
        """Test streak returns zero when no data."""
        streak = scoring_system.get_streak(date.today())
        assert streak == 0

    def test_streak_zero_score_breaks(self, scoring_system):
        """Test that zero score breaks streak."""
        # Day with zero score (no completed tasks)
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task", completed=False, estimated_seconds=600, actual_seconds=0)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        streak = scoring_system.get_streak(date.today())
        assert streak == 0


class TestGetDailyScore:
    """Test retrieving daily scores."""

    def test_get_daily_score_exists(self, scoring_system):
        """Test retrieving existing daily score."""
        task_list = DailyTaskList(
            date=date(2025, 1, 15),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        original_score = scoring_system.calculate_daily_score(task_list)

        retrieved_score = scoring_system.get_daily_score(date(2025, 1, 15))
        assert retrieved_score is not None
        assert retrieved_score.total_score == original_score.total_score

    def test_get_daily_score_not_exists(self, scoring_system):
        """Test retrieving non-existent daily score."""
        score = scoring_system.get_daily_score(date(2025, 1, 15))
        assert score is None


class TestAverageEfficiency:
    """Test average efficiency calculation."""

    def test_average_efficiency_single_day(self, scoring_system):
        """Test average efficiency with single day."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        avg_eff = scoring_system.get_average_efficiency(days=7)
        # 300 / 600 = 0.5 efficiency
        assert abs(avg_eff - 0.5) < 0.01

    def test_average_efficiency_multiple_days(self, scoring_system):
        """Test average efficiency across multiple days."""
        # Day 1: efficiency = 0.5 (300/600)
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        # Day 2: efficiency = 1.0 (600/600)
        task_list = DailyTaskList(
            date=date.today() - timedelta(days=1),
            tasks=[
                Task("Task", completed=True, estimated_seconds=600, actual_seconds=600)
            ]
        )
        scoring_system.calculate_daily_score(task_list)

        avg_eff = scoring_system.get_average_efficiency(days=7)
        # Average of 0.5 and 1.0 = 0.75
        assert abs(avg_eff - 0.75) < 0.01

    def test_average_efficiency_limits_to_n_days(self, scoring_system):
        """Test that average efficiency only considers last N days."""
        # Add 10 days of data
        for i in range(10):
            task_list = DailyTaskList(
                date=date.today() - timedelta(days=i),
                tasks=[
                    Task("Task", completed=True, estimated_seconds=600, actual_seconds=600)
                ]
            )
            scoring_system.calculate_daily_score(task_list)

        # Request only last 3 days
        avg_eff = scoring_system.get_average_efficiency(days=3)
        # Should only consider 3 most recent days
        assert abs(avg_eff - 1.0) < 0.01

    def test_average_efficiency_no_data(self, scoring_system):
        """Test average efficiency with no data."""
        avg_eff = scoring_system.get_average_efficiency(days=7)
        assert avg_eff == 1.0  # Default value


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_save_stats_io_error(self, tmp_path):
        """Test that IO errors during save don't crash the app."""
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        stats_file = readonly_dir / "stats.json"

        scorer = ScoringSystem(stats_file=stats_file)

        # Make directory read-only (on Unix-like systems)
        import os
        if os.name != 'nt':  # Skip on Windows
            readonly_dir.chmod(0o444)

            task_list = DailyTaskList(
                date=date.today(),
                tasks=[Task("Task", completed=True, estimated_seconds=600, actual_seconds=300)]
            )
            # Should not crash even if save fails
            scorer.calculate_daily_score(task_list)

            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_very_large_time_values(self, scoring_system):
        """Test scoring with very large time values."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                Task("Long task", completed=True, estimated_seconds=86400, actual_seconds=43200)
            ]
        )
        daily_score = scoring_system.calculate_daily_score(task_list)

        # Should handle large values without errors
        assert daily_score.total_estimated_minutes == 1440  # 24 hours
        assert daily_score.total_actual_minutes == 720  # 12 hours

    def test_score_with_fractional_seconds(self, scoring_system):
        """Test that scoring handles fractional seconds correctly."""
        task_list = DailyTaskList(
            date=date.today(),
            tasks=[
                # 5.5 minutes estimated, 3.5 minutes actual
                Task("Task", completed=True, estimated_seconds=330, actual_seconds=210)
            ]
        )
        daily_score = scoring_system.calculate_daily_score(task_list)

        # Minutes are converted via int division
        assert daily_score.total_estimated_minutes == 5
        assert daily_score.total_actual_minutes == 3
