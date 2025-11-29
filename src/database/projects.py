"""Project database operations."""

import streamlit as st
from .connection import get_db
from typing import List, Dict, Any, Optional


def get_user_projects(user_id: Optional[str] = None, include_shared: bool = True) -> List[Dict[str, Any]]:
    """
    Get projects for the current user (owned + shared).

    Args:
        user_id: Optional user ID (uses session state if not provided)
        include_shared: Whether to include projects shared with the user

    Returns:
        List of project records with 'is_shared' flag
    """
    try:
        if not user_id and "user" in st.session_state and st.session_state.user:
            user_id = st.session_state.user.get("id")

        if not user_id:
            return []

        db = get_db()

        # Get owned projects
        owned_response = db.table("projects").select(
            "*, grants(id, name, name_en)"
        ).eq("user_id", user_id).order("updated_at", desc=True).execute()

        owned_projects = owned_response.data or []
        for p in owned_projects:
            p["is_shared"] = False
            p["access_level"] = "owner"

        if not include_shared:
            return owned_projects

        # Get shared projects
        shared_response = db.table("project_shares").select(
            "access_level, projects!inner(*, grants(id, name, name_en), profiles!projects_user_id_fkey(email, full_name))"
        ).eq("user_id", user_id).execute()

        shared_projects = []
        for share in (shared_response.data or []):
            project = share.get("projects", {})
            if project:
                project["is_shared"] = True
                project["access_level"] = share.get("access_level", "read")
                project["owner_info"] = project.pop("profiles", None)
                shared_projects.append(project)

        # Combine and sort by updated_at
        all_projects = owned_projects + shared_projects
        all_projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return all_projects
    except Exception as e:
        print(f"Error fetching user projects: {e}")
        return []


def get_all_projects() -> List[Dict[str, Any]]:
    """
    Get all projects (admin use).

    Returns:
        List of all project records with user and grant info
    """
    try:
        db = get_db()
        response = db.table("projects").select(
            "*, grants(id, name, name_en), profiles(id, email, full_name)"
        ).order("updated_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching all projects: {e}")
        return []


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


def create_project(
    grant_id: str,
    name: str,
    description: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Create a new project for the current user.

    Args:
        grant_id: Grant UUID
        name: Project name
        description: Project description

    Returns:
        Created project record or None
    """
    user = st.session_state.get("user")
    if not user:
        raise Exception("User not authenticated")

    db = get_db()
    response = db.table("projects").insert({
        "user_id": user["id"],
        "grant_id": grant_id,
        "name": name,
        "description": description,
        "status": "draft"
    }).execute()
    return response.data[0] if response.data else None


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


def delete_project(project_id: str) -> bool:
    """
    Delete a project and all related data.

    Args:
        project_id: Project UUID

    Returns:
        True if successful
    """
    try:
        db = get_db()
        db.table("projects").delete().eq("id", project_id).execute()
        return True
    except Exception:
        return False
