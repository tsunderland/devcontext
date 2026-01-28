"""Formatting utilities for DevContext."""

from datetime import datetime, timedelta


def format_time_ago(dt: datetime) -> str:
    """Format a datetime as a human-readable 'time ago' string."""
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"


def format_duration(start: datetime, end: datetime) -> str:
    """Format the duration between two datetimes."""
    diff = end - start

    total_seconds = int(diff.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}m"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes:
            return f"{hours}h {minutes}m"
        return f"{hours}h"


def format_file_list(files: list[str], max_display: int = 5) -> str:
    """Format a list of files for display."""
    if not files:
        return "None"

    if len(files) <= max_display:
        return "\n".join(f"  • {f}" for f in files)

    displayed = "\n".join(f"  • {f}" for f in files[:max_display])
    remaining = len(files) - max_display
    return f"{displayed}\n  ... and {remaining} more"
