"""Project database operations (worker version - no streamlit)."""

from .connection import get_db
from typing import List, Dict, Any, Optional


def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Get project by ID with all related data.

    Args:
        project_id: Project UUID

    Returns:
        Project record with grants, documents, and results
    """
    try:
        db = get_db()
        response = db.table("projects").select(
            "*, grants(*, grant_requirements(*)), project_documents(*), project_results(*)"
        ).eq("id", project_id).single().execute()
        return response.data
    except Exception:
        return None


def update_project(project_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Update a project.

    Args:
        project_id: Project UUID
        **kwargs: Fields to update

    Returns:
        Updated project record or None
    """
    try:
        db = get_db()
        response = db.table("projects").update(kwargs).eq("id", project_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating project: {e}")
        return None


def calculate_completion(project_id: str) -> int:
    """
    Calculate project completion percentage based on filled infobits.

    Args:
        project_id: Project UUID

    Returns:
        Completion percentage (0-100)
    """
    try:
        db = get_db()
        response = db.table("project_infobits").select("value, is_required").eq(
            "project_id", project_id
        ).execute()

        infobits = response.data or []
        if not infobits:
            return 0

        required = [ib for ib in infobits if ib.get("is_required", True)]
        if not required:
            return 100

        filled = sum(1 for ib in required if ib.get("value"))
        return int((filled / len(required)) * 100)
    except Exception as e:
        print(f"Error calculating completion: {e}")
        return 0
