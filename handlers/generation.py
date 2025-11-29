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

    task_data format (legacy):
    {
        "language": "et",
        "generate_docx": true,
        "generate_xlsx": true
    }

    task_data format (new):
    {
        "output_type": "application_docx_from_sections" | "budget_xlsx"
    }

    Returns:
        {"docx_path": "...", "xlsx_path": "..."}
    """
    from src.ai.document_generator import DocumentGenerator
    from src.storage.supabase_storage import upload_project_doc
    from src.database.projects import get_project_by_id, update_project
    from src.database.documents import create_project_result

    language = task_data.get("language", "et")

    # Support both new output_type format and legacy format
    output_type = task_data.get("output_type")
    if output_type:
        generate_docx = output_type == "application_docx"
        generate_xlsx = output_type == "budget_xlsx"
        generate_from_sections = output_type == "application_docx_from_sections"
        generate_cover_letter = output_type == "cover_letter_docx"
        generate_executive_summary = output_type == "executive_summary_docx"
        generate_timeline = output_type == "timeline_xlsx"
        generate_risk_analysis = output_type == "risk_analysis_docx"
    else:
        generate_docx = task_data.get("generate_docx", True)
        generate_xlsx = task_data.get("generate_xlsx", False)
        generate_from_sections = False
        generate_cover_letter = False
        generate_executive_summary = False
        generate_timeline = False
        generate_risk_analysis = False

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

    # Generate from pre-edited sections
    if generate_from_sections:
        from src.database.sections import get_project_sections

        progress_callback(20, "Loading sections...")
        sections = get_project_sections(project_id)

        if not sections:
            raise Exception("No sections found for this project")

        progress_callback(40, "Generating application document from sections...")

        docx_bytes = generator.generate_docx_from_sections(
            project_name=project.get("name", "Application"),
            grant_name=grant.get("name", ""),
            sections=sections
        )

        if docx_bytes:
            progress_callback(60, "Saving DOCX...")
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
                    result_type="application_docx_from_sections",
                    file_path=file_path
                )
                result["docx_path"] = file_path

    # Generate traditional DOCX (AI-generated content)
    elif generate_docx:
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

    # Generate cover letter
    if generate_cover_letter:
        progress_callback(20, "Generating cover letter...")

        docx_bytes = generator.generate_cover_letter_docx(
            project=project,
            requirements_text=requirements_text
        )

        if docx_bytes:
            progress_callback(60, "Saving cover letter...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cover_letter_{timestamp}.docx"

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
                    result_type="cover_letter_docx",
                    file_path=file_path
                )
                result["cover_letter_path"] = file_path

    # Generate executive summary
    if generate_executive_summary:
        progress_callback(20, "Generating executive summary...")

        docx_bytes = generator.generate_executive_summary_docx(
            project=project,
            requirements_text=requirements_text
        )

        if docx_bytes:
            progress_callback(60, "Saving executive summary...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"executive_summary_{timestamp}.docx"

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
                    result_type="executive_summary_docx",
                    file_path=file_path
                )
                result["executive_summary_path"] = file_path

    # Generate timeline
    if generate_timeline:
        progress_callback(20, "Generating timeline...")

        xlsx_bytes = generator.generate_timeline_xlsx(
            project=project,
            requirements_text=requirements_text
        )

        if xlsx_bytes:
            progress_callback(60, "Saving timeline...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"timeline_{timestamp}.xlsx"

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
                    result_type="timeline_xlsx",
                    file_path=file_path
                )
                result["timeline_path"] = file_path

    # Generate risk analysis
    if generate_risk_analysis:
        progress_callback(20, "Generating risk analysis...")

        docx_bytes = generator.generate_risk_analysis_docx(
            project=project,
            requirements_text=requirements_text
        )

        if docx_bytes:
            progress_callback(60, "Saving risk analysis...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_analysis_{timestamp}.docx"

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
                    result_type="risk_analysis_docx",
                    file_path=file_path
                )
                result["risk_analysis_path"] = file_path

    # Update project status
    if result:
        update_project(project_id, status="completed")

    progress_callback(100, "Generation complete")

    return result
