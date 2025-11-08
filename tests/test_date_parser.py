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

    # TODO: Add tests for:
    # - Day names (monday, tuesday, etc.)
    # - Month + day (nov 10, december 25)
    # - Edge cases (empty string, whitespace)
