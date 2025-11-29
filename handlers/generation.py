"""Handler for document generation tasks."""

from typing import Dict, Any, Callable
from datetime import datetime


def handle_generation(
    db,
    task_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    progress_callback: Callable[[int, str], None]
) -> Dict[str, Any]:
    """
    Generate application documents (DOCX and/or XLSX).

    task_data format:
    {
        "language": "et",
        "generate_docx": true,
        "generate_xlsx": true
    }

    Returns:
        {"docx_path": "...", "xlsx_path": "..."}
    """
    from src.ai.document_generator import DocumentGenerator
    from src.storage.supabase_storage import upload_project_doc
    from src.database.projects import get_project_by_id, update_project
    from src.database.documents import create_project_result

    language = task_data.get("language", "et")
    generate_docx = task_data.get("generate_docx", True)
    generate_xlsx = task_data.get("generate_xlsx", False)

    progress_callback(0, "Loading project data...")

    # Get project
    project = get_project_by_id(project_id)
    if not project:
        raise Exception("Project not found")

    # Compile requirements text
    grant = project.get("grants", {})
    requirements = grant.get("grant_requirements", [])
    requirements_text = ""
    for req in requirements:
        requirements_text += f"\n## {req.get('name', '')}\n"
        requirements_text += f"{req.get('description', '')}\n"

    generator = DocumentGenerator(language=language)
    result = {}

    if generate_docx:
        progress_callback(20, "Generating application document...")

        docx_bytes = generator.generate_application_docx(
            project=project,
            requirements_text=requirements_text
        )

        if docx_bytes:
            progress_callback(40, "Saving DOCX...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"application_{timestamp}.docx"

            file_path = upload_project_doc(
                user_id,
                project_id,
                docx_bytes,
                filename,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            if file_path:
                create_project_result(
                    project_id=project_id,
                    result_type="application_docx",
                    file_path=file_path
                )
                result["docx_path"] = file_path

    if generate_xlsx:
        progress_callback(60, "Generating budget spreadsheet...")

        xlsx_bytes = generator.generate_budget_xlsx(
            project=project,
            requirements_text=requirements_text
        )

        if xlsx_bytes:
            progress_callback(80, "Saving XLSX...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"budget_{timestamp}.xlsx"

            file_path = upload_project_doc(
                user_id,
                project_id,
                xlsx_bytes,
                filename,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            if file_path:
                create_project_result(
                    project_id=project_id,
                    result_type="budget_xlsx",
                    file_path=file_path
                )
                result["xlsx_path"] = file_path

    # Update project status
    if result:
        update_project(project_id, status="completed")

    progress_callback(100, "Generation complete")

    return result
