"""Grant database operations."""

from .connection import get_db
from typing import List, Dict, Any, Optional


def get_active_grants() -> List[Dict[str, Any]]:
    """
    Get all active grants.

    Returns:
        List of active grant records
    """
    try:
        db = get_db()
        response = db.table("grants").select("*").eq("is_active", True).order("name").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching grants: {e}")
        return []


def get_all_grants() -> List[Dict[str, Any]]:
    """
    Get all grants (including inactive) - for admin use.

    Returns:
        List of all grant records
    """
    try:
        db = get_db()
        response = db.table("grants").select("*, grant_requirements(*)").order("name").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching all grants: {e}")
        return []


def get_grant_by_id(grant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get grant by ID with requirements.

    Args:
        grant_id: Grant UUID

    Returns:
        Grant record with requirements or None
    """
    try:
        db = get_db()
        response = db.table("grants").select("*, grant_requirements(*)").eq("id", grant_id).single().execute()
        return response.data
    except Exception:
        return None


def create_grant(
    name: str,
    description: str,
    eis_link: str = "",
    name_en: str = "",
    description_en: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Create a new grant.

    Args:
        name: Grant name (Estonian)
        description: Grant description (Estonian)
        eis_link: EIS website link
        name_en: Grant name (English)
        description_en: Grant description (English)

    Returns:
        Created grant record or None
    """
    db = get_db()
    data = {
        "name": name,
        "description": description,
        "eis_link": eis_link
    }
    if name_en:
        data["name_en"] = name_en
    if description_en:
        data["description_en"] = description_en

    response = db.table("grants").insert(data).execute()
    return response.data[0] if response.data else None


def update_grant(grant_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Update a grant.

    Args:
        grant_id: Grant UUID
        **kwargs: Fields to update

    Returns:
        Updated grant record or None
    """
    try:
        db = get_db()
        response = db.table("grants").update(kwargs).eq("id", grant_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating grant: {e}")
        return None


def delete_grant(grant_id: str) -> bool:
    """
    Delete a grant.

    Args:
        grant_id: Grant UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("grants").delete().eq("id", grant_id).execute()
        return True
    except Exception:
        return False


def get_grant_requirements(grant_id: str) -> List[Dict[str, Any]]:
    """
    Get all requirements for a grant.

    Args:
        grant_id: Grant UUID

    Returns:
        List of requirement records
    """
    try:
        db = get_db()
        response = db.table("grant_requirements").select("*").eq(
            "grant_id", grant_id
        ).order("sort_order").execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching grant requirements: {e}")
        return []


def create_grant_requirement(
    grant_id: str,
    name: str,
    file_path: str = "",
    file_type: str = "",
    description: str = "",
    name_en: str = "",
    description_en: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Create a new grant requirement.

    Args:
        grant_id: Parent grant UUID
        name: Requirement name
        file_path: Path to requirement document in storage
        file_type: File type (PDF, DOCX, etc.)
        description: Requirement description
        name_en: Name in English
        description_en: Description in English

    Returns:
        Created requirement record or None
    """
    try:
        db = get_db()
        data = {
            "grant_id": grant_id,
            "name": name,
            "file_path": file_path,
            "file_type": file_type,
            "description": description
        }
        if name_en:
            data["name_en"] = name_en
        if description_en:
            data["description_en"] = description_en

        response = db.table("grant_requirements").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating requirement: {e}")
        return None


def update_grant_requirement(requirement_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Update a grant requirement.

    Args:
        requirement_id: Requirement UUID
        **kwargs: Fields to update

    Returns:
        Updated requirement record or None
    """
    try:
        db = get_db()
        response = db.table("grant_requirements").update(kwargs).eq("id", requirement_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating requirement: {e}")
        return None


def delete_grant_requirement(requirement_id: str) -> bool:
    """
    Delete a grant requirement.

    Args:
        requirement_id: Requirement UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("grant_requirements").delete().eq("id", requirement_id).execute()
        return True
    except Exception:
        return False


# ============================================
# GRANT EXAMPLES (example documents for AI reference)
# ============================================

def get_grant_examples(grant_id: str) -> List[Dict[str, Any]]:
    """
    Get all example documents for a grant.

    Args:
        grant_id: Grant UUID

    Returns:
        List of example documents
    """
    try:
        db = get_db()
        response = db.table("grant_examples").select("*").eq("grant_id", grant_id).order("created_at").execute()
        return response.data or []
    except Exception:
        return []


def create_grant_example(
    grant_id: str,
    name: str,
    file_path: str,
    file_type: str = "",
    description: str = "",
    extracted_text: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Create a new grant example document.

    Args:
        grant_id: Parent grant UUID
        name: Example document name
        file_path: Path to document in storage
        file_type: File type (PDF, DOCX, etc.)
        description: Description of what this example demonstrates
        extracted_text: Extracted text content from document

    Returns:
        Created example record or None
    """
    try:
        db = get_db()
        data = {
            "grant_id": grant_id,
            "name": name,
            "file_path": file_path,
            "file_type": file_type,
            "description": description,
            "extracted_text": extracted_text
        }
        response = db.table("grant_examples").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating example: {e}")
        return None


def delete_grant_example(example_id: str) -> bool:
    """
    Delete a grant example document.

    Args:
        example_id: Example UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("grant_examples").delete().eq("id", example_id).execute()
        return True
    except Exception:
        return False
