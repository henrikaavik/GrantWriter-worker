"""Infobits database operations."""

from .connection import get_db
from typing import List, Dict, Any, Optional


def create_infobits(project_id: str, infobits: List[Dict[str, Any]]) -> bool:
    """
    Create infobits for a project.

    Args:
        project_id: Project UUID
        infobits: List of infobit definitions

    Returns:
        True if successful
    """
    try:
        db = get_db()
        records = []
        for infobit in infobits:
            records.append({
                "project_id": project_id,
                "field_name": infobit.get("field_name"),
                "field_label": infobit.get("field_label"),
                "field_label_en": infobit.get("field_label_en", ""),
                "field_description": infobit.get("field_description", ""),
                "category": infobit.get("category", "general"),
                "is_required": infobit.get("is_required", True),
                "value": infobit.get("value", ""),
                "source": infobit.get("source", "manual"),
                "sort_order": infobit.get("sort_order", 0),
            })

        if records:
            db.table("project_infobits").insert(records).execute()
        return True
    except Exception as e:
        print(f"Error creating infobits: {e}")
        return False


def get_project_infobits(project_id: str) -> List[Dict[str, Any]]:
    """
    Get all infobits for a project.

    Args:
        project_id: Project UUID

    Returns:
        List of infobit records
    """
    try:
        db = get_db()
        response = db.table("project_infobits").select("*").eq(
            "project_id", project_id
        ).order("category").order("sort_order").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching infobits: {e}")
        return []


def get_infobits_by_category(project_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get infobits grouped by category.

    Args:
        project_id: Project UUID

    Returns:
        Dictionary with category as key and list of infobits as value
    """
    infobits = get_project_infobits(project_id)
    grouped = {}
    for infobit in infobits:
        category = infobit.get("category", "general")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(infobit)
    return grouped


def get_empty_infobits(project_id: str) -> List[Dict[str, Any]]:
    """
    Get infobits that have no value filled.

    Args:
        project_id: Project UUID

    Returns:
        List of empty infobit records
    """
    try:
        db = get_db()
        response = db.table("project_infobits").select("*").eq(
            "project_id", project_id
        ).eq("value", "").order("category").order("sort_order").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching empty infobits: {e}")
        return []


def update_infobit(
    infobit_id: str,
    value: str,
    source: str = "manual",
    confidence: Optional[float] = None
) -> bool:
    """
    Update an infobit value.

    Args:
        infobit_id: Infobit UUID
        value: New value
        source: Source of value ('manual', 'ai_extracted', etc.)
        confidence: Confidence score if AI-extracted

    Returns:
        True if successful
    """
    try:
        db = get_db()
        update_data = {
            "value": value,
            "source": source,
            "updated_at": "now()",
        }
        if confidence is not None:
            update_data["confidence"] = confidence

        db.table("project_infobits").update(update_data).eq(
            "id", infobit_id
        ).execute()
        return True
    except Exception as e:
        print(f"Error updating infobit: {e}")
        return False


def update_infobit_by_field_name(
    project_id: str,
    field_name: str,
    value: str,
    source: str = "manual",
    confidence: Optional[float] = None
) -> bool:
    """
    Update an infobit by field name.

    Args:
        project_id: Project UUID
        field_name: Field name identifier
        value: New value
        source: Source of value
        confidence: Confidence score if AI-extracted

    Returns:
        True if successful
    """
    try:
        db = get_db()
        update_data = {
            "value": value,
            "source": source,
            "updated_at": "now()",
        }
        if confidence is not None:
            update_data["confidence"] = confidence

        db.table("project_infobits").update(update_data).eq(
            "project_id", project_id
        ).eq("field_name", field_name).execute()
        return True
    except Exception as e:
        print(f"Error updating infobit by field name: {e}")
        return False


def calculate_completion(project_id: str) -> int:
    """
    Calculate completion percentage for a project's infobits.

    Args:
        project_id: Project UUID

    Returns:
        Completion percentage (0-100)
    """
    try:
        infobits = get_project_infobits(project_id)
        if not infobits:
            return 0

        # Count required fields that are filled
        required_count = 0
        filled_count = 0

        for infobit in infobits:
            if infobit.get("is_required", True):
                required_count += 1
                if infobit.get("value", "").strip():
                    filled_count += 1

        if required_count == 0:
            return 100

        return int((filled_count / required_count) * 100)
    except Exception as e:
        print(f"Error calculating completion: {e}")
        return 0


def delete_project_infobits(project_id: str) -> bool:
    """
    Delete all infobits for a project.

    Args:
        project_id: Project UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("project_infobits").delete().eq("project_id", project_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting infobits: {e}")
        return False


def get_infobit_by_id(infobit_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single infobit by ID.

    Args:
        infobit_id: Infobit UUID

    Returns:
        Infobit record or None
    """
    try:
        db = get_db()
        response = db.table("project_infobits").select("*").eq(
            "id", infobit_id
        ).single().execute()
        return response.data
    except Exception:
        return None
