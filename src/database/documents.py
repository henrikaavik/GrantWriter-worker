"""Document database operations."""

from .connection import get_db
from typing import List, Dict, Any, Optional


def get_project_documents(project_id: str) -> List[Dict[str, Any]]:
    """
    Get all documents for a project.

    Args:
        project_id: Project UUID

    Returns:
        List of document records
    """
    try:
        db = get_db()
        response = db.table("project_documents").select("*").eq(
            "project_id", project_id
        ).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching project documents: {e}")
        return []


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get document by ID.

    Args:
        document_id: Document UUID

    Returns:
        Document record or None
    """
    try:
        db = get_db()
        response = db.table("project_documents").select("*").eq(
            "id", document_id
        ).single().execute()
        return response.data
    except Exception:
        return None


def create_project_document(
    project_id: str,
    name: str,
    file_path: str,
    file_type: str = "",
    file_size: int = 0,
    extracted_text: str = "",
    requirement_id: str = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new project document record.

    Args:
        project_id: Project UUID
        name: Document name
        file_path: Path to file in storage
        file_type: File type (PDF, DOCX, etc.)
        file_size: File size in bytes
        extracted_text: Extracted text content
        requirement_id: Optional linked requirement UUID

    Returns:
        Created document record or None
    """
    try:
        db = get_db()
        data = {
            "project_id": project_id,
            "name": name,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "extracted_text": extracted_text
        }
        if requirement_id:
            data["requirement_id"] = requirement_id

        response = db.table("project_documents").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating project document: {e}")
        return None


def update_project_document(document_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Update a project document.

    Args:
        document_id: Document UUID
        **kwargs: Fields to update

    Returns:
        Updated document record or None
    """
    try:
        db = get_db()
        response = db.table("project_documents").update(kwargs).eq(
            "id", document_id
        ).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating project document: {e}")
        return None


def delete_project_document(document_id: str) -> bool:
    """
    Delete a project document.

    Args:
        document_id: Document UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("project_documents").delete().eq("id", document_id).execute()
        return True
    except Exception:
        return False


def get_project_results(project_id: str) -> List[Dict[str, Any]]:
    """
    Get all results for a project.

    Args:
        project_id: Project UUID

    Returns:
        List of result records
    """
    try:
        db = get_db()
        response = db.table("project_results").select("*").eq(
            "project_id", project_id
        ).order("generated_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching project results: {e}")
        return []


def create_project_result(
    project_id: str,
    result_type: str,
    file_path: str
) -> Optional[Dict[str, Any]]:
    """
    Create a new project result record.

    Args:
        project_id: Project UUID
        result_type: Type of result (application_docx, budget_xlsx, etc.)
        file_path: Path to file in storage

    Returns:
        Created result record or None
    """
    try:
        db = get_db()
        response = db.table("project_results").insert({
            "project_id": project_id,
            "result_type": result_type,
            "file_path": file_path
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating project result: {e}")
        return None


def delete_project_result(result_id: str) -> bool:
    """
    Delete a project result.

    Args:
        result_id: Result UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("project_results").delete().eq("id", result_id).execute()
        return True
    except Exception:
        return False
