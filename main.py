"""
Background worker service for GrantWriter.
Polls Supabase task_queue and processes tasks.
"""

import os
import sys
import time
import uuid
from datetime import datetime

from supabase import create_client

WORKER_ID = str(uuid.uuid4())[:8]
POLL_INTERVAL = 5  # seconds


def get_db():
    """Get Supabase client."""
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"]
    )


def claim_task(db):
    """Atomically claim a pending task."""
    try:
        result = db.rpc("claim_next_task", {"worker": WORKER_ID}).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error claiming task: {e}")
        return None


def update_task_progress(db, task_id: str, progress: int, message: str):
    """Update task progress."""
    try:
        db.table("task_queue").update({
            "progress": progress,
            "progress_message": message
        }).eq("id", task_id).execute()
    except Exception as e:
        print(f"Error updating progress: {e}")


def complete_task(db, task_id: str, result_data: dict):
    """Mark task as completed."""
    try:
        db.table("task_queue").update({
            "status": "completed",
            "progress": 100,
            "result_data": result_data,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()
    except Exception as e:
        print(f"Error completing task: {e}")


def fail_task(db, task_id: str, error_message: str):
    """Mark task as failed."""
    try:
        db.table("task_queue").update({
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()
    except Exception as e:
        print(f"Error failing task: {e}")


def process_task(db, task: dict):
    """Process a single task."""
    task_id = task["id"]
    task_type = task["task_type"]
    task_data = task["task_data"]
    user_id = task.get("user_id")
    project_id = task.get("project_id")

    print(f"[{WORKER_ID}] Processing {task_type} task {task_id}")

    try:
        # Import handlers lazily to avoid circular imports
        from handlers import (
            handle_infobit_extraction,
            handle_infobit_generation,
            handle_evaluation,
            handle_generation,
            handle_requirement_extraction
        )

        handlers = {
            "infobit_extraction": handle_infobit_extraction,
            "infobit_generation": handle_infobit_generation,
            "evaluation": handle_evaluation,
            "generation": handle_generation,
            "requirement_extraction": handle_requirement_extraction,
        }

        handler = handlers.get(task_type)
        if not handler:
            fail_task(db, task_id, f"Unknown task type: {task_type}")
            return

        # Create progress callback
        def progress_callback(progress: int, message: str):
            update_task_progress(db, task_id, progress, message)

        # Execute handler
        result = handler(
            db=db,
            task_data=task_data,
            user_id=user_id,
            project_id=project_id,
            progress_callback=progress_callback
        )

        complete_task(db, task_id, result)
        print(f"[{WORKER_ID}] Completed task {task_id}")

    except Exception as e:
        print(f"[{WORKER_ID}] Error processing task {task_id}: {e}")
        fail_task(db, task_id, str(e))


def recover_stale_tasks(db):
    """Reset tasks stuck in 'processing' status (from crashed workers)."""
    try:
        # Find tasks stuck in processing for more than 2 minutes
        from datetime import timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()

        result = db.table("task_queue").select("id, task_type, started_at").eq(
            "status", "processing"
        ).lt("started_at", cutoff).execute()

        stale_tasks = result.data or []
        if stale_tasks:
            print(f"🔄 Found {len(stale_tasks)} stale tasks to recover", flush=True)
            for task in stale_tasks:
                db.table("task_queue").update({
                    "status": "pending",
                    "progress": 0,
                    "progress_message": "Requeued after worker restart",
                    "worker_id": None
                }).eq("id", task["id"]).execute()
                print(f"  ↩️ Reset task {task['id']} ({task['task_type']})", flush=True)
    except Exception as e:
        print(f"⚠️ Error recovering stale tasks: {e}", flush=True)


def main():
    """Main worker loop."""
    print(f"🚀 Worker {WORKER_ID} starting...", flush=True)
    print(f"📊 Poll interval: {POLL_INTERVAL}s", flush=True)

    # Verify environment variables
    if not os.environ.get("SUPABASE_URL"):
        print("❌ ERROR: SUPABASE_URL not set!", flush=True)
        sys.exit(1)
    if not os.environ.get("SUPABASE_KEY"):
        print("❌ ERROR: SUPABASE_KEY not set!", flush=True)
        sys.exit(1)

    print("✅ Environment variables OK", flush=True)

    try:
        db = get_db()
        print("✅ Connected to Supabase", flush=True)
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}", flush=True)
        sys.exit(1)

    # Recover any stuck tasks from previous worker crashes
    recover_stale_tasks(db)

    print("👀 Polling for tasks...", flush=True)

    while True:
        try:
            task = claim_task(db)
            if task:
                print(f"📋 Claimed task: {task.get('id')}", flush=True)
                process_task(db, task)
            else:
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print(f"\n👋 Worker {WORKER_ID} shutting down...", flush=True)
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}", flush=True)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
