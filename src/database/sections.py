"""Project sections database operations for worker."""

from .connection import get_db
from typing import List, Dict, Any


def get_project_sections(project_id: str) -> List[Dict[str, Any]]:
    """
    Get all sections for a project, ordered by sort_order.

    Args:
        project_id: Project UUID

    Returns:
        List of section records
    """
    try:
        db = get_db()
        response = db.table("project_sections").select("*").eq(
            "project_id", project_id
        ).order("sort_order").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching sections: {e}")
        return []
