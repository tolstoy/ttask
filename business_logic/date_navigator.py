"""Date navigation and parsing logic for task journal."""
import re
from datetime import date, timedelta
from typing import Optional
from markdown_handler import MarkdownHandler
from config import config


class DateNavigator:
    """Handles date-based navigation operations."""

    def __init__(self, handler: MarkdownHandler):
        """
        Initialize DateNavigator.

        Args:
            handler: MarkdownHandler instance for loading tasks
        """
        self.handler = handler

    def find_prev_non_empty_day(
        self, start_date: date, max_days: Optional[int] = None
    ) -> Optional[date]:
        """
        Find the previous day that has incomplete tasks.

        Args:
            start_date: Date to start searching from
            max_days: Maximum number of days to search backwards (uses config.max_search_days if None)

        Returns:
            Date of previous day with incomplete tasks, or None if not found
        """
        if max_days is None:
            max_days = config.max_search_days

        check_date = start_date - timedelta(days=1)
        for _ in range(max_days):
            file_path = self.handler.get_file_path(check_date)
            if file_path.exists():
                # Check if file has tasks with at least one incomplete
                daily_list = self.handler.load_tasks(check_date)
                if daily_list.tasks and any(not task.completed for task in daily_list.tasks):
                    return check_date
            check_date -= timedelta(days=1)
        return None

    def find_next_non_empty_day(
        self, start_date: date, max_days: Optional[int] = None
    ) -> Optional[date]:
        """
        Find the next day that has incomplete tasks.

        Args:
            start_date: Date to start searching from
            max_days: Maximum number of days to search forward (uses config.max_search_days if None)

        Returns:
            Date of next day with incomplete tasks, or None if not found
        """
        if max_days is None:
            max_days = config.max_search_days

        check_date = start_date + timedelta(days=1)
        for _ in range(max_days):
            file_path = self.handler.get_file_path(check_date)
            if file_path.exists():
                # Check if file has tasks with at least one incomplete
                daily_list = self.handler.load_tasks(check_date)
                if daily_list.tasks and any(not task.completed for task in daily_list.tasks):
                    return check_date
            check_date += timedelta(days=1)
        return None


class NaturalDateParser:
    """Parse natural language date inputs."""

    @staticmethod
    def parse(input_str: str, from_date: date) -> Optional[date]:
        """
        Parse natural language date input.

        Supports:
        - Relative offsets: +1, -1, +7, etc. (relative to from_date, the viewed date)
        - ISO format: YYYY-MM-DD (absolute)
        - Absolute words: today, tomorrow, yesterday (relative to actual current date)
        - Day names: monday, tuesday, etc. (next occurrence from actual current date)
        - Relative weeks: next week, last week (relative to actual current date)
        - Month + day: nov 10, december 25 (current year based on actual current date)

        Args:
            input_str: Natural language date string
            from_date: Reference date for relative offsets

        Returns:
            Parsed date or None if parsing failed
        """
        input_str = input_str.strip().lower()

        # Try relative offset (+1, -1, etc.)
        if input_str.startswith('+') or input_str.startswith('-'):
            try:
                days = int(input_str)
                return from_date + timedelta(days=days)
            except ValueError:
                pass

        # Try ISO format (YYYY-MM-DD)
        try:
            return date.fromisoformat(input_str)
        except ValueError:
            pass

        # Absolute date words (relative to actual current date, not viewed date)
        today = date.today()
        if input_str == "today":
            return today
        elif input_str == "tomorrow":
            return today + timedelta(days=1)
        elif input_str == "yesterday":
            return today - timedelta(days=1)
        elif input_str == "next week":
            return today + timedelta(days=7)
        elif input_str == "last week":
            return today - timedelta(days=7)

        # Day names (next occurrence)
        day_names = {
            "monday": 0, "mon": 0,
            "tuesday": 1, "tue": 1, "tues": 1,
            "wednesday": 2, "wed": 2,
            "thursday": 3, "thu": 3, "thurs": 3,
            "friday": 4, "fri": 4,
            "saturday": 5, "sat": 5,
            "sunday": 6, "sun": 6
        }

        if input_str in day_names:
            target_weekday = day_names[input_str]
            today = date.today()
            current_weekday = today.weekday()
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return today + timedelta(days=days_ahead)

        # Month + day (e.g., "nov 10", "december 25")
        month_names = {
            "jan": 1, "january": 1,
            "feb": 2, "february": 2,
            "mar": 3, "march": 3,
            "apr": 4, "april": 4,
            "may": 5,
            "jun": 6, "june": 6,
            "jul": 7, "july": 7,
            "aug": 8, "august": 8,
            "sep": 9, "sept": 9, "september": 9,
            "oct": 10, "october": 10,
            "nov": 11, "november": 11,
            "dec": 12, "december": 12
        }

        # Try to match "month day" pattern
        pattern = r'^(\w+)\s+(\d{1,2})$'
        match = re.match(pattern, input_str)
        if match:
            month_str, day_str = match.groups()
            if month_str in month_names:
                try:
                    month = month_names[month_str]
                    day = int(day_str)
                    today = date.today()
                    year = today.year
                    # Try to create the date
                    target_date = date(year, month, day)
                    # If the date is in the past, use next year
                    if target_date < today:
                        target_date = date(year + 1, month, day)
                    return target_date
                except ValueError:
                    pass

        return None
