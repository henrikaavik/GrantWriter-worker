"""Supabase authentication utilities (worker version - minimal, no streamlit).

Worker doesn't need full auth - it uses service credentials.
This file provides stubs for any imports that might reference it.
"""

from typing import Optional, Dict, Any


def get_current_user() -> Optional[Dict[str, Any]]:
    """Worker doesn't have a current user - returns None."""
    return None


def is_authenticated() -> bool:
    """Worker is always authenticated via service credentials."""
    return True


def is_admin() -> bool:
    """Worker has admin-level access."""
    return True
