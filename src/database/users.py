"""User database operations."""

from .connection import get_db
from typing import List, Dict, Any, Optional


def get_all_users() -> List[Dict[str, Any]]:
    """
    Get all user profiles (admin use).

    Returns:
        List of user profile records
    """
    try:
        db = get_db()
        response = db.table("profiles").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile by ID.

    Args:
        user_id: User UUID

    Returns:
        User profile record or None
    """
    try:
        db = get_db()
        response = db.table("profiles").select("*").eq("id", user_id).single().execute()
        return response.data
    except Exception:
        return None


def update_user_profile(user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Update user profile.

    Args:
        user_id: User UUID
        **kwargs: Fields to update

    Returns:
        Updated profile record or None
    """
    try:
        db = get_db()
        response = db.table("profiles").update(kwargs).eq("id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return None


def update_user_role(user_id: str, role: str) -> bool:
    """
    Update user role.

    Args:
        user_id: User UUID
        role: New role ('pending', 'user' or 'admin')

    Returns:
        True if successful
    """
    if role not in ["pending", "user", "admin"]:
        print(f"Invalid role: {role}")
        return False

    try:
        db = get_db()
        response = db.table("profiles").update({"role": role}).eq("id", user_id).execute()
        print(f"Update role response: {response.data}")
        return True
    except Exception as e:
        print(f"Error updating user role: {e}")
        return False


def delete_user(user_id: str) -> bool:
    """
    Delete a user profile (for rejecting pending users).

    Args:
        user_id: User UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("profiles").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False


def get_user_count() -> int:
    """
    Get total number of users.

    Returns:
        User count
    """
    try:
        db = get_db()
        response = db.table("profiles").select("id", count="exact").execute()
        return response.count or 0
    except Exception:
        return 0
