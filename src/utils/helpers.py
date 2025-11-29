"""Utility helper functions (worker version - no streamlit)."""

from typing import Optional, Union
from datetime import datetime


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_datetime(dt: Optional[Union[datetime, str]]) -> str:
    """Format datetime for display."""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M")


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""
