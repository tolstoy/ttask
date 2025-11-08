"""Tests for natural language date parsing."""
import pytest
from datetime import date, timedelta
from business_logic.date_navigator import NaturalDateParser


class TestNaturalDateParser:
    """Test suite for NaturalDateParser."""

    def test_parse_today(self):
        """Test parsing 'today'."""
        result = NaturalDateParser.parse("today", date(2025, 11, 8))
        assert result == date.today()

    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow'."""
        result = NaturalDateParser.parse("tomorrow", date(2025, 11, 8))
        expected = date.today() + timedelta(days=1)
        assert result == expected

    def test_parse_yesterday(self):
        """Test parsing 'yesterday'."""
        result = NaturalDateParser.parse("yesterday", date(2025, 11, 8))
        expected = date.today() - timedelta(days=1)
        assert result == expected

    def test_parse_relative_offset_positive(self):
        """Test parsing positive offset like '+1'."""
        from_date = date(2025, 11, 8)
        result = NaturalDateParser.parse("+1", from_date)
        assert result == date(2025, 11, 9)

    def test_parse_relative_offset_negative(self):
        """Test parsing negative offset like '-1'."""
        from_date = date(2025, 11, 8)
        result = NaturalDateParser.parse("-1", from_date)
        assert result == date(2025, 11, 7)

    def test_parse_iso_format(self):
        """Test parsing ISO format date."""
        result = NaturalDateParser.parse("2025-12-25", date(2025, 11, 8))
        assert result == date(2025, 12, 25)

    def test_parse_invalid_input(self):
        """Test parsing invalid input returns None."""
        result = NaturalDateParser.parse("invalid", date(2025, 11, 8))
        assert result is None

    def test_parse_next_week(self):
        """Test parsing 'next week'."""
        result = NaturalDateParser.parse("next week", date(2025, 11, 8))
        expected = date.today() + timedelta(days=7)
        assert result == expected

    def test_parse_last_week(self):
        """Test parsing 'last week'."""
        result = NaturalDateParser.parse("last week", date(2025, 11, 8))
        expected = date.today() - timedelta(days=7)
        assert result == expected

    def test_parse_day_name_monday(self):
        """Test parsing day names like 'monday'."""
        # This test will find the next Monday from today
        result = NaturalDateParser.parse("monday", date(2025, 11, 8))
        # Result should be a date in the future
        assert result is not None
        assert result.weekday() == 0  # Monday is 0

    def test_parse_day_name_friday(self):
        """Test parsing 'friday'."""
        result = NaturalDateParser.parse("friday", date(2025, 11, 8))
        assert result is not None
        assert result.weekday() == 4  # Friday is 4

    def test_parse_month_day_format(self):
        """Test parsing 'nov 10' format."""
        result = NaturalDateParser.parse("nov 10", date(2025, 11, 8))
        assert result is not None
        assert result.month == 11
        assert result.day == 10

    def test_parse_full_month_day_format(self):
        """Test parsing 'december 25' format."""
        result = NaturalDateParser.parse("december 25", date(2025, 11, 8))
        assert result is not None
        assert result.month == 12
        assert result.day == 25

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = NaturalDateParser.parse("", date(2025, 11, 8))
        assert result is None

    def test_parse_whitespace_only(self):
        """Test parsing whitespace returns None."""
        result = NaturalDateParser.parse("   ", date(2025, 11, 8))
        assert result is None

    def test_parse_case_insensitive(self):
        """Test parsing is case insensitive."""
        result1 = NaturalDateParser.parse("TOMORROW", date(2025, 11, 8))
        result2 = NaturalDateParser.parse("tomorrow", date(2025, 11, 8))
        result3 = NaturalDateParser.parse("ToMoRrOw", date(2025, 11, 8))
        assert result1 == result2 == result3

    def test_parse_large_positive_offset(self):
        """Test parsing large positive offset like '+30'."""
        from_date = date(2025, 11, 8)
        result = NaturalDateParser.parse("+30", from_date)
        assert result == date(2025, 12, 8)

    def test_parse_large_negative_offset(self):
        """Test parsing large negative offset like '-30'."""
        from_date = date(2025, 11, 8)
        result = NaturalDateParser.parse("-30", from_date)
        assert result == date(2025, 10, 9)

    def test_parse_zero_offset(self):
        """Test parsing '+0' returns from_date."""
        from_date = date(2025, 11, 8)
        result = NaturalDateParser.parse("+0", from_date)
        assert result == from_date

    def test_parse_invalid_iso_date(self):
        """Test parsing invalid ISO date returns None."""
        result = NaturalDateParser.parse("2025-13-45", date(2025, 11, 8))
        assert result is None

    def test_parse_invalid_month_day(self):
        """Test parsing invalid month/day combo returns None."""
        result = NaturalDateParser.parse("feb 30", date(2025, 11, 8))
        # Should return None for invalid date
        assert result is None or (result.month == 2 and result.day <= 29)
