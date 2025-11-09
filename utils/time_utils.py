"""Time parsing and formatting utilities for taskjournal."""

import re
from typing import Optional


def parse_time_string(time_str: str) -> Optional[int]:
    """
    Parse a time string into seconds.

    Supports formats:
    - Plain number: "30" -> 30 minutes -> 1800 seconds
    - Seconds: "90s" or "90sec" -> 90 seconds
    - Minutes: "30m" or "30min" -> 1800 seconds
    - Hours: "2h" -> 7200 seconds
    - Combined: "1h30m15s" -> 5415 seconds
    - Decimal: "1.5h" -> 5400 seconds, "2.5m" -> 150 seconds

    Args:
        time_str: Time string to parse

    Returns:
        Number of seconds, or None if parse fails
    """
    time_str = time_str.strip().lower()
    if not time_str:
        return None

    # Try plain number first (assumes minutes, convert to seconds)
    try:
        return int(time_str) * 60
    except ValueError:
        pass

    # Try to parse with units
    # Match patterns like: 1h30m15s, 2h, 30m, 90s, 1.5h, etc.
    # Pattern: optional hours, optional minutes, optional seconds
    pattern = r'(?:(\d+(?:\.\d+)?)(?:h|hr|hour|hours))?\s*(?:(\d+(?:\.\d+)?)(?:m|min|minutes?))?\s*(?:(\d+(?:\.\d+)?)(?:s|sec|seconds?))?'
    match = re.match(pattern, time_str)

    if match:
        hours_str, minutes_str, seconds_str = match.groups()
        total_seconds = 0.0

        if hours_str:
            total_seconds += float(hours_str) * 3600
        if minutes_str:
            total_seconds += float(minutes_str) * 60
        if seconds_str:
            total_seconds += float(seconds_str)

        if total_seconds > 0:
            return int(total_seconds)

    return None


def format_time(seconds: int) -> str:
    """
    Format seconds into human-readable string.

    Returns format like "1h 30m" or "45m" or "30s".
    Hours and minutes are separated by space for readability.
    Seconds are only shown if less than 60 seconds total or if there's a remainder.

    Args:
        seconds: Number of seconds to format

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds}s"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0:
        parts.append(f"{secs}s")

    return "".join(parts)
