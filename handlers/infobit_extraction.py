"""Handler for infobit extraction tasks."""

import gc
from typing import Dict, Any, Callable


def handle_infobit_extraction(
    db,
    task_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    progress_callback: Callable[[int, str], None]
) -> Dict[str, Any]:
    """
    Extract infobits from uploaded documents.

    task_data format:
    {
        "files": [
            {"name": "doc.pdf", "path": "storage/path"}
        ],
        "language": "et"
    }

    Returns:
        {"files_processed": N, "fields_filled": M}
    """
    from src.ai.infobit_extractor import extract_infobits_from_document
    from src.storage.supabase_storage import download_file
    from src.database.infobits import get_empty_infobits, update_infobit, calculate_completion
    from src.database.projects import update_project

    files = task_data.get("files", [])
    language = task_data.get("language", "et")

    progress_callback(0, "Starting extraction...")

    # Get empty infobits for this project
    empty_infobits = get_empty_infobits(project_id)
    total_filled = 0
    processed_files = 0

    for i, file_info in enumerate(files):
        file_name = file_info.get("name", "unknown")
        file_path = file_info.get("path", "")

        progress_pct = int((i / len(files)) * 90)
        progress_callback(progress_pct, f"Processing: {file_name}")

        # Download file from storage
        file_data = download_file("project-documents", file_path)
        if not file_data:
            print(f"Could not download file: {file_path}")
            continue

        processed_files += 1

        # Extract infobits
        result = extract_infobits_from_document(
            file_data, file_name, empty_infobits, language
        )

        if result and result.extractions:
            for ext in result.extractions:
                # Find matching infobit and update
                for infobit in empty_infobits:
                    if infobit["field_name"] == ext.field_name:
                        update_infobit(
                            infobit["id"],
                            ext.extracted_value,
                            source=f"ai:{file_name[:15]}",
                            confidence=ext.confidence
                        )
                        total_filled += 1
                        # Remove from empty list to avoid overwriting
                        empty_infobits = [
                            ib for ib in empty_infobits
                            if ib["id"] != infobit["id"]
                        ]
                        break

        # Free memory between files to prevent OOM on Render free tier
        del file_data
        gc.collect()

    # Update project completion
    progress_callback(95, "Updating completion...")
    from src.database.infobits import calculate_completion
    new_completion = calculate_completion(project_id)
    update_project(project_id, infobits_completion=new_completion)

    progress_callback(100, "Complete")

    return {
        "files_processed": processed_files,
        "fields_filled": total_filled
    }
