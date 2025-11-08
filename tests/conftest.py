"""Pytest configuration and shared fixtures."""
import pytest
from datetime import date
from models import Task, DailyTaskList


@pytest.fixture
def sample_tasks():
    """Fixture providing a sample list of tasks."""
    return [
        Task("Buy groceries", completed=False, indent_level=0),
        Task("Milk", completed=False, indent_level=1),
        Task("Eggs", completed=False, indent_level=1),
        Task("Call mom", completed=True, indent_level=0),
        Task("Write email", completed=False, indent_level=0),
    ]


@pytest.fixture
def sample_daily_list(sample_tasks):
    """Fixture providing a DailyTaskList with sample tasks."""
    return DailyTaskList(date=date.today(), tasks=sample_tasks)


@pytest.fixture
def empty_daily_list():
    """Fixture providing an empty DailyTaskList."""
    return DailyTaskList(date=date.today(), tasks=[])
