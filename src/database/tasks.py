"""Task queue database operations."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from .connection import get_db


def create_task(
    user_id: str,
    project_id: str,
    task_type: str,
    task_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Create a new task in the queue.

    Args:
        user_id: ID of the user who submitted the task
        project_id: ID of the related project
        task_type: Type of task (infobit_extraction, evaluation, generation, requirement_extraction)
        task_data: Task-specific input data

    Returns:
        Created task record or None on error
    """
    db = get_db()
    try:
        result = db.table("task_queue").insert({
            "user_id": user_id,
            "project_id": project_id,
            "task_type": task_type,
            "task_data": task_data
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating task: {e}")
        return None


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a task by ID."""
    db = get_db()
    try:
        result = db.table("task_queue").select("*").eq("id", task_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting task: {e}")
        return None


def get_user_tasks(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get tasks for a user, optionally filtered by status."""
    db = get_db()
    try:
        query = db.table("task_queue").select("*").eq("user_id", user_id)
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting user tasks: {e}")
        return []


def get_project_tasks(
    project_id: str,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get tasks for a project, optionally filtered by status."""
    db = get_db()
    try:
        query = db.table("task_queue").select("*").eq("project_id", project_id)
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting project tasks: {e}")
        return []


def get_active_task(project_id: str, task_type: str) -> Optional[Dict[str, Any]]:
    """Get an active (pending or processing) task of a specific type for a project."""
    db = get_db()
    try:
        result = db.table("task_queue").select("*").eq("project_id", project_id).eq("task_type", task_type).in_("status", ["pending", "processing"]).order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting active task: {e}")
        return None


def update_task_progress(
    task_id: str,
    progress: int,
    message: str
) -> bool:
    """Update task progress."""
    db = get_db()
    try:
        db.table("task_queue").update({
            "progress": progress,
            "progress_message": message
        }).eq("id", task_id).execute()
        return True
    except Exception as e:
        print(f"Error updating task progress: {e}")
        return False


def complete_task(
    task_id: str,
    result_data: Dict[str, Any]
) -> bool:
    """Mark a task as completed."""
    db = get_db()
    try:
        db.table("task_queue").update({
            "status": "completed",
            "progress": 100,
            "result_data": result_data,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()
        return True
    except Exception as e:
        print(f"Error completing task: {e}")
        return False


def fail_task(task_id: str, error_message: str) -> bool:
    """Mark a task as failed."""
    db = get_db()
    try:
        db.table("task_queue").update({
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()
        return True
    except Exception as e:
        print(f"Error failing task: {e}")
        return False


def cancel_task(task_id: str) -> bool:
    """Cancel a pending task."""
    db = get_db()
    try:
        db.table("task_queue").update({
            "status": "cancelled",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).eq("status", "pending").execute()
        return True
    except Exception as e:
        print(f"Error cancelling task: {e}")
        return False


def claim_next_task(worker_id: str) -> Optional[Dict[str, Any]]:
    """Atomically claim the next pending task using database function."""
    db = get_db()
    try:
        result = db.rpc("claim_next_task", {"worker": worker_id}).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error claiming task: {e}")
        return None
