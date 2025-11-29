"""Project sharing database operations."""

from typing import List, Dict, Any, Optional
from .connection import get_db


def get_project_shares(project_id: str) -> List[Dict[str, Any]]:
    """
    Get all users who have access to a project.

    Args:
        project_id: The project UUID

    Returns:
        List of share records with user info
    """
    try:
        db = get_db()
        response = db.table("project_shares").select(
            "*, profiles!project_shares_user_id_fkey(id, email, full_name)"
        ).eq("project_id", project_id).execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting project shares: {e}")
        return []


def get_shared_projects_for_user(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all projects shared with a user.

    Args:
        user_id: The user UUID

    Returns:
        List of project records
    """
    try:
        db = get_db()
        response = db.table("project_shares").select(
            "*, projects!inner(*, grants(name, name_en)), profiles!project_shares_user_id_fkey(id, email, full_name)"
        ).eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting shared projects: {e}")
        return []


def share_project(project_id: str, user_id: str, granted_by: str, access_level: str = "read") -> bool:
    """
    Share a project with a user.

    Args:
        project_id: The project UUID
        user_id: The user UUID to share with
        granted_by: The admin user UUID who granted access
        access_level: 'read' or 'write'

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("project_shares").upsert({
            "project_id": project_id,
            "user_id": user_id,
            "granted_by": granted_by,
            "access_level": access_level
        }).execute()
        return True
    except Exception as e:
        print(f"Error sharing project: {e}")
        return False


def revoke_project_access(project_id: str, user_id: str) -> bool:
    """
    Revoke a user's access to a project.

    Args:
        project_id: The project UUID
        user_id: The user UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("project_shares").delete().eq(
            "project_id", project_id
        ).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error revoking access: {e}")
        return False


def has_project_access(project_id: str, user_id: str) -> bool:
    """
    Check if a user has access to a project (owned or shared).

    Args:
        project_id: The project UUID
        user_id: The user UUID

    Returns:
        True if user has access
    """
    try:
        db = get_db()

        # Check if user owns the project
        project = db.table("projects").select("id").eq(
            "id", project_id
        ).eq("user_id", user_id).execute()

        if project.data:
            return True

        # Check if project is shared with user
        share = db.table("project_shares").select("id").eq(
            "project_id", project_id
        ).eq("user_id", user_id).execute()

        return bool(share.data)
    except Exception as e:
        print(f"Error checking project access: {e}")
        return False


def get_access_level(project_id: str, user_id: str) -> Optional[str]:
    """
    Get user's access level for a project.

    Args:
        project_id: The project UUID
        user_id: The user UUID

    Returns:
        'owner', 'read', 'write', or None if no access
    """
    try:
        db = get_db()

        # Check if user owns the project
        project = db.table("projects").select("id").eq(
            "id", project_id
        ).eq("user_id", user_id).execute()

        if project.data:
            return "owner"

        # Check shared access
        share = db.table("project_shares").select("access_level").eq(
            "project_id", project_id
        ).eq("user_id", user_id).execute()

        if share.data:
            return share.data[0]["access_level"]

        return None
    except Exception as e:
        print(f"Error getting access level: {e}")
        return None


def get_all_projects_for_admin() -> List[Dict[str, Any]]:
    """
    Get all projects with owner info (for admin).

    Returns:
        List of all projects with owner details
    """
    try:
        db = get_db()
        response = db.table("projects").select(
            "*, grants(name, name_en), profiles!projects_user_id_fkey(id, email, full_name)"
        ).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting all projects: {e}")
        return []


def get_all_users_for_admin() -> List[Dict[str, Any]]:
    """
    Get all users (for admin dropdowns).

    Returns:
        List of all users
    """
    try:
        db = get_db()
        response = db.table("profiles").select(
            "id, email, full_name, role"
        ).order("email").execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
