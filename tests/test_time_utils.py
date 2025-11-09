"""Tests for time parsing and formatting utilities."""

import pytest
from utils.time_utils import parse_time_string, format_time


class TestParseTimeString:
    """Test time string parsing."""

    def test_parse_plain_number(self):
        """Plain numbers should be interpreted as minutes."""
        assert parse_time_string("30") == 1800  # 30 minutes = 1800 seconds
        assert parse_time_string("1") == 60  # 1 minute = 60 seconds
        assert parse_time_string("90") == 5400  # 90 minutes = 5400 seconds

    def test_parse_seconds(self):
        """Test parsing seconds with various formats."""
        assert parse_time_string("30s") == 30
        assert parse_time_string("90s") == 90
        assert parse_time_string("45sec") == 45
        assert parse_time_string("60seconds") == 60

    def test_parse_minutes(self):
        """Test parsing minutes with various formats."""
        assert parse_time_string("5m") == 300
        assert parse_time_string("30m") == 1800
        assert parse_time_string("2min") == 120
        assert parse_time_string("10minutes") == 600

    def test_parse_hours(self):
        """Test parsing hours with various formats."""
        assert parse_time_string("1h") == 3600
        assert parse_time_string("2h") == 7200
        assert parse_time_string("1hr") == 3600
        assert parse_time_string("3hours") == 10800

    def test_parse_combined(self):
        """Test parsing combined time formats."""
        assert parse_time_string("1h30m") == 5400  # 1.5 hours
        assert parse_time_string("1h30m15s") == 5415
        assert parse_time_string("2h15m") == 8100
        assert parse_time_string("30m45s") == 1845

    def test_parse_decimal(self):
        """Test parsing decimal time formats."""
        assert parse_time_string("1.5h") == 5400  # 1.5 hours = 90 minutes
        assert parse_time_string("2.5m") == 150  # 2.5 minutes = 150 seconds
        assert parse_time_string("0.5h") == 1800  # 0.5 hours = 30 minutes

    def test_parse_with_spaces(self):
        """Test parsing with spaces between components."""
        assert parse_time_string("1h 30m") == 5400
        assert parse_time_string("2h 15m 30s") == 8130

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        assert parse_time_string("30M") == 1800
        assert parse_time_string("1H") == 3600
        assert parse_time_string("45S") == 45
        assert parse_time_string("1H30M") == 5400

    def test_parse_invalid(self):
        """Test parsing invalid inputs."""
        assert parse_time_string("") is None
        assert parse_time_string("invalid") is None
        assert parse_time_string("abc") is None
        assert parse_time_string("h") is None
        assert parse_time_string("m") is None

    def test_parse_edge_cases(self):
        """Test edge cases."""
        assert parse_time_string(" ") is None
        assert parse_time_string("0") == 0
        # Note: "0h", "0m", "0s" return None because total_seconds is 0 which fails the > 0 check
        assert parse_time_string("0h") is None
        assert parse_time_string("0m") is None
        assert parse_time_string("0s") is None


class TestFormatTime:
    """Test time formatting."""

    def test_format_seconds_only(self):
        """Test formatting when less than 60 seconds."""
        assert format_time(0) == "0s"
        assert format_time(30) == "30s"
        assert format_time(45) == "45s"
        assert format_time(59) == "59s"

    def test_format_minutes_only(self):
        """Test formatting when minutes but no hours or seconds remainder."""
        assert format_time(60) == "1m"
        assert format_time(120) == "2m"
        assert format_time(1800) == "30m"
        assert format_time(3000) == "50m"

    def test_format_minutes_and_seconds(self):
        """Test formatting with both minutes and seconds."""
        assert format_time(90) == "1m30s"
        assert format_time(125) == "2m5s"
        assert format_time(1845) == "30m45s"

    def test_format_hours_only(self):
        """Test formatting when exactly hours with no remainder."""
        assert format_time(3600) == "1h"
        assert format_time(7200) == "2h"
        assert format_time(10800) == "3h"

    def test_format_hours_and_minutes(self):
        """Test formatting with hours and minutes."""
        assert format_time(5400) == "1h30m"
        assert format_time(7800) == "2h10m"
        assert format_time(9000) == "2h30m"

    def test_format_hours_minutes_seconds(self):
        """Test formatting with all components."""
        assert format_time(5415) == "1h30m15s"
        assert format_time(7325) == "2h2m5s"
        assert format_time(3665) == "1h1m5s"

    def test_format_hours_and_seconds(self):
        """Test formatting with hours and seconds but no minutes."""
        assert format_time(3615) == "1h15s"
        assert format_time(7245) == "2h45s"


class TestRoundTrip:
    """Test that parsing and formatting are consistent."""

    def test_round_trip_simple(self):
        """Test round trip for simple formats."""
        # Note: plain numbers are interpreted as minutes
        original = "30"
        seconds = parse_time_string(original)
        formatted = format_time(seconds)
        assert parse_time_string(formatted) == seconds

    def test_round_trip_with_units(self):
        """Test round trip for formats with units."""
        test_cases = ["30s", "5m", "2h", "1h30m", "1h30m15s", "45m30s"]
        for original in test_cases:
            seconds = parse_time_string(original)
            formatted = format_time(seconds)
            # Parse the formatted string and compare seconds
            assert parse_time_string(formatted) == seconds

    def test_round_trip_decimal(self):
        """Test round trip for decimal formats."""
        # Decimal formats may not round-trip exactly to the same string,
        # but should round-trip to the same number of seconds
        test_cases = ["1.5h", "2.5m", "0.5h"]
        for original in test_cases:
            seconds = parse_time_string(original)
            formatted = format_time(seconds)
            # Verify we can parse the formatted version back to same seconds
            assert parse_time_string(formatted) == seconds
