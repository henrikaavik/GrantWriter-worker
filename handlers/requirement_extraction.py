"""Handler for grant requirement extraction tasks."""

from typing import Dict, Any, Callable


def handle_requirement_extraction(
    db,
    task_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    progress_callback: Callable[[int, str], None]
) -> Dict[str, Any]:
    """
    Extract checklist items from grant requirement documents.

    task_data format:
    {
        "requirement_ids": ["uuid1", "uuid2"],  # Or empty to process all unprocessed
        "language": "et"
    }

    Returns:
        {"requirements_processed": N, "items_extracted": M}
    """
    from src.ai.requirements_extractor import RequirementsExtractor
    from src.database.grants import get_grant_requirements, update_grant_requirement

    requirement_ids = task_data.get("requirement_ids", [])
    language = task_data.get("language", "et")

    progress_callback(0, "Starting extraction...")

    # Get requirements to process
    if requirement_ids:
        # Process specific requirements
        requirements = []
        for rid in requirement_ids:
            req = db.table("grant_requirements").select("*").eq("id", rid).execute()
            if req.data:
                requirements.append(req.data[0])
    else:
        # Get all requirements that need processing
        result = db.table("grant_requirements").select("*").is_("extracted_checklist", "null").execute()
        requirements = result.data or []

    if not requirements:
        progress_callback(100, "No requirements to process")
        return {"requirements_processed": 0, "items_extracted": 0}

    extractor = RequirementsExtractor(language=language)
    total_items = 0
    processed_count = 0

    for i, req in enumerate(requirements):
        req_name = req.get("name", "unknown")
        progress_pct = int((i / len(requirements)) * 90)
        progress_callback(progress_pct, f"Processing: {req_name}")

        file_path = req.get("file_path")
        if not file_path:
            continue

        # Extract requirements
        result = extractor.process_requirement_document(
            requirement_id=req["id"],
            file_path=file_path
        )

        if result and result.checklist:
            total_items += len(result.checklist)
            processed_count += 1

    progress_callback(100, "Extraction complete")

    return {
        "requirements_processed": processed_count,
        "items_extracted": total_items
    }
