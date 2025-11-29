"""Evaluate user documents against grant requirements."""

from typing import Dict, Any, Optional, List
from .gemini_client import GeminiService, DocumentEvaluation
from src.database.documents import update_project_document
from src.database.projects import update_project, get_project_by_id


class DocumentEvaluator:
    """Evaluate user documents against grant requirements."""

    def __init__(self, language: str = "et"):
        """
        Initialize document evaluator.

        Args:
            language: Language for AI responses ('et' or 'en')
        """
        self.gemini = GeminiService(language)

    def evaluate_document(
        self,
        document_id: str,
        document_text: str,
        document_name: str,
        requirements_text: str
    ) -> Optional[DocumentEvaluation]:
        """
        Evaluate a single document.

        Args:
            document_id: ID of the project_document record
            document_text: Extracted text content of the document
            document_name: Name of the document
            requirements_text: Text of grant requirements

        Returns:
            DocumentEvaluation or None on error
        """
        if not document_text:
            return None

        # Evaluate using AI
        evaluation = self.gemini.evaluate_document(
            document_text=document_text,
            requirements_text=requirements_text,
            document_name=document_name
        )

        if evaluation:
            # Save evaluation to database
            update_project_document(
                document_id,
                ai_evaluation=evaluation.model_dump(),
                document_score=evaluation.score,
                annotations=[ann.model_dump() for ann in evaluation.annotations],
                comments={
                    "summary": evaluation.summary,
                    "strengths": evaluation.strengths,
                    "weaknesses": evaluation.weaknesses,
                    "recommendations": evaluation.recommendations
                }
            )

        return evaluation

    def evaluate_all_project_documents(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate all documents in a project and calculate overall score.

        Args:
            project_id: ID of the project

        Returns:
            Dict with evaluations and overall score
        """
        project = get_project_by_id(project_id)
        if not project:
            return {"evaluations": [], "overall_score": None}

        # Compile requirements text
        requirements_text = self._compile_requirements_text(project)

        evaluations = []
        total_score = 0
        evaluated_count = 0

        # Evaluate each document
        for doc in project.get("project_documents", []):
            doc_text = doc.get("extracted_text", "")

            if doc_text:
                evaluation = self.evaluate_document(
                    document_id=doc["id"],
                    document_text=doc_text,
                    document_name=doc["name"],
                    requirements_text=requirements_text
                )

                if evaluation:
                    evaluations.append(evaluation)
                    total_score += evaluation.score
                    evaluated_count += 1

        # Calculate overall score
        overall_score = None
        if evaluated_count > 0:
            overall_score = total_score / evaluated_count
            update_project(project_id, overall_score=overall_score)

        return {
            "evaluations": evaluations,
            "overall_score": overall_score,
            "evaluated_count": evaluated_count
        }

    def _compile_requirements_text(self, project: dict) -> str:
        """
        Compile all requirements into a single text.

        Args:
            project: Project data with grants and requirements

        Returns:
            Compiled requirements text
        """
        grant = project.get("grants", {})
        requirements = grant.get("grant_requirements", [])

        texts = []
        texts.append(f"# Grant: {grant.get('name', 'Unknown')}")

        if grant.get("description"):
            texts.append(f"\n{grant['description']}\n")

        for req in requirements:
            texts.append(f"\n## {req.get('name', 'Requirement')}")

            if req.get("description"):
                texts.append(req["description"])

            checklist = req.get("extracted_checklist", [])
            if checklist:
                texts.append("\nChecklist:")
                for item in checklist:
                    if isinstance(item, dict):
                        name = item.get("name", "")
                        desc = item.get("description", "")
                        mandatory = "MANDATORY" if item.get("is_mandatory") else "Optional"
                        texts.append(f"- [{mandatory}] {name}: {desc}")
                    else:
                        texts.append(f"- {item}")

        return "\n".join(texts)
