"""AI usage tracking database operations."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .connection import get_db

# Gemini pricing (per 1M tokens) - approximate as of 2024
PRICING = {
    "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a given model and token counts."""
    pricing = PRICING.get(model, PRICING["gemini-2.0-flash"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def log_ai_usage(
    user_id: str,
    operation: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Log AI usage for tracking expenses.

    Args:
        user_id: ID of the user
        operation: Type of operation (infobit_extraction, evaluation, etc.)
        model: Model used (gemini-2.0-flash, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        project_id: Optional project ID
        task_id: Optional task ID

    Returns:
        Created record or None on error
    """
    db = get_db()
    cost = calculate_cost(model, input_tokens, output_tokens)

    try:
        data = {
            "user_id": user_id,
            "operation": operation,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost
        }
        if project_id:
            data["project_id"] = project_id
        if task_id:
            data["task_id"] = task_id

        result = db.table("ai_usage").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error logging AI usage: {e}")
        return None


def get_user_usage_summary(
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """Get usage summary for a user over the past N days."""
    db = get_db()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    try:
        result = db.table("ai_usage").select("*").eq("user_id", user_id).gte("created_at", since).execute()
        records = result.data or []

        total_input = sum(r.get("input_tokens", 0) for r in records)
        total_output = sum(r.get("output_tokens", 0) for r in records)
        total_cost = sum(float(r.get("cost_usd", 0)) for r in records)

        by_operation = {}
        for r in records:
            op = r.get("operation", "unknown")
            if op not in by_operation:
                by_operation[op] = {"count": 0, "cost": 0}
            by_operation[op]["count"] += 1
            by_operation[op]["cost"] += float(r.get("cost_usd", 0))

        return {
            "total_requests": len(records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": total_cost,
            "by_operation": by_operation
        }
    except Exception as e:
        print(f"Error getting user usage: {e}")
        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0,
            "by_operation": {}
        }


def get_project_usage_summary(project_id: str) -> Dict[str, Any]:
    """Get total usage for a project."""
    db = get_db()

    try:
        result = db.table("ai_usage").select("*").eq("project_id", project_id).execute()
        records = result.data or []

        total_input = sum(r.get("input_tokens", 0) for r in records)
        total_output = sum(r.get("output_tokens", 0) for r in records)
        total_cost = sum(float(r.get("cost_usd", 0)) for r in records)

        return {
            "total_requests": len(records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": total_cost
        }
    except Exception as e:
        print(f"Error getting project usage: {e}")
        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0
        }


def get_all_users_usage(days: int = 30) -> List[Dict[str, Any]]:
    """Get usage summary for all users (admin view)."""
    db = get_db()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    try:
        # Get all usage records
        result = db.table("ai_usage").select("user_id, input_tokens, output_tokens, cost_usd").gte("created_at", since).execute()
        records = result.data or []

        # Group by user
        by_user = {}
        for r in records:
            uid = r.get("user_id")
            if uid not in by_user:
                by_user[uid] = {
                    "user_id": uid,
                    "total_requests": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost_usd": 0
                }
            by_user[uid]["total_requests"] += 1
            by_user[uid]["total_input_tokens"] += r.get("input_tokens", 0)
            by_user[uid]["total_output_tokens"] += r.get("output_tokens", 0)
            by_user[uid]["total_cost_usd"] += float(r.get("cost_usd", 0))

        return list(by_user.values())
    except Exception as e:
        print(f"Error getting all users usage: {e}")
        return []


def get_total_usage(days: int = 30) -> Dict[str, Any]:
    """Get total usage across all users."""
    db = get_db()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    try:
        result = db.table("ai_usage").select("input_tokens, output_tokens, cost_usd").gte("created_at", since).execute()
        records = result.data or []

        return {
            "total_requests": len(records),
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in records),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in records),
            "total_cost_usd": sum(float(r.get("cost_usd", 0)) for r in records)
        }
    except Exception as e:
        print(f"Error getting total usage: {e}")
        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0
        }
