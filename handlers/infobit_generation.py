"""Handler for infobit generation tasks."""

from typing import Dict, Any, Callable


def handle_infobit_generation(
    db,
    task_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    progress_callback: Callable[[int, str], None]
) -> Dict[str, Any]:
    """
    Generate infobits for a newly created project.

    task_data format:
    {
        "grant_id": "uuid",
        "language": "et"
    }

    Returns:
        {"infobits_count": N}
    """
    from src.ai.infobit_generator import generate_infobits_for_grant, get_default_infobits
    from src.database.infobits import create_infobits
    from src.database.projects import update_project

    grant_id = task_data.get("grant_id")
    language = task_data.get("language", "et")

    progress_callback(10, "Analyzing grant requirements...")

    # Try AI generation first
    generated = generate_infobits_for_grant(grant_id, language)

    progress_callback(60, "Creating infobit fields...")

    if generated and generated.infobits:
        # Convert to dict format
        infobits_data = [
            {
                "field_name": ib.field_name,
                "field_label": ib.field_label,
                "field_label_en": ib.field_label_en,
                "field_description": ib.field_description,
                "category": ib.category,
                "is_required": ib.is_required,
                "sort_order": ib.sort_order,
            }
            for ib in generated.infobits
        ]
    else:
        # Fall back to defaults
        infobits_data = get_default_infobits(language)

    progress_callback(80, "Saving to database...")

    # Save to database
    create_infobits(project_id, infobits_data)

    # Mark project as having infobits generated
    update_project(project_id, infobits_generated=True)

    progress_callback(100, "Complete")

    return {
        "infobits_count": len(infobits_data)
    }
