"""Handler for document evaluation tasks."""

from typing import Dict, Any, Callable


def handle_evaluation(
    db,
    task_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    progress_callback: Callable[[int, str], None]
) -> Dict[str, Any]:
    """
    Evaluate project documents against grant requirements.

    task_data format:
    {
        "language": "et"
    }

    Returns:
        {"documents_evaluated": N, "overall_score": X.X}
    """
    from src.ai.document_evaluator import DocumentEvaluator
    from src.ai.document_parser import DocumentParser
    from src.storage.supabase_storage import download_file
    from src.database.projects import get_project_by_id, update_project
    from src.database.documents import get_project_documents, update_project_document

    language = task_data.get("language", "et")

    progress_callback(0, "Loading project data...")

    # Get project and documents
    project = get_project_by_id(project_id)
    if not project:
        raise Exception("Project not found")

    documents = get_project_documents(project_id)
    if not documents:
        raise Exception("No documents found")

    # Compile requirements text
    grant = project.get("grants", {})
    requirements = grant.get("grant_requirements", [])
    requirements_text = ""
    for req in requirements:
        requirements_text += f"\n## {req.get('name', '')}\n"
        requirements_text += f"{req.get('description', '')}\n"
        checklist = req.get("extracted_checklist", [])
        for item in checklist:
            if isinstance(item, dict):
                requirements_text += f"- {item.get('name', '')}: {item.get('description', '')}\n"
            else:
                requirements_text += f"- {item}\n"

    # Initialize evaluator
    evaluator = DocumentEvaluator(language=language)
    parser = DocumentParser()

    total_score = 0
    evaluated_count = 0
    scores = []

    for i, doc in enumerate(documents):
        doc_name = doc.get("name", "unknown")
        progress_pct = int((i / len(documents)) * 90)
        progress_callback(progress_pct, f"Evaluating: {doc_name}")

        # Get or extract document text
        doc_text = doc.get("extracted_text", "")

        if not doc_text:
            # Extract text from document
            file_data = download_file("project-documents", doc["file_path"])
            if file_data:
                parsed = parser.parse_document(file_data, doc_name)
                doc_text = parsed.get("text", "")
                if doc_text:
                    update_project_document(doc["id"], extracted_text=doc_text)

        if not doc_text:
            continue

        # Evaluate document
        evaluation = evaluator.evaluate_document(
            document_id=doc["id"],
            document_text=doc_text,
            document_name=doc_name,
            requirements_text=requirements_text
        )

        if evaluation:
            total_score += evaluation.score
            evaluated_count += 1
            scores.append({
                "document": doc_name,
                "score": evaluation.score
            })

    # Calculate and save overall score
    overall_score = None
    if evaluated_count > 0:
        overall_score = total_score / evaluated_count
        update_project(project_id, overall_score=overall_score)

    progress_callback(100, "Evaluation complete")

    return {
        "documents_evaluated": evaluated_count,
        "overall_score": overall_score,
        "scores": scores
    }
