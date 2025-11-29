"""Gemini AI client for document analysis and generation."""

import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from ..utils.secrets import get_gemini_api_key


def get_gemini_client():
    """Get Gemini client instance."""
    api_key = get_gemini_api_key()
    return genai.Client(api_key=api_key)


# Pydantic models for structured output
class RequirementItem(BaseModel):
    """Single requirement item."""
    name: str = Field(description="Name of the requirement")
    description: str = Field(description="Detailed description of what is needed")
    is_mandatory: bool = Field(description="Whether this requirement is mandatory")


class ExtractedRequirements(BaseModel):
    """Extracted requirements from grant documentation."""
    checklist: List[RequirementItem] = Field(description="List of requirements")
    summary: str = Field(description="Brief summary of all requirements")


class DocumentAnnotation(BaseModel):
    """Annotation for a specific part of a document."""
    text_segment: str = Field(description="The text being annotated (max 100 chars)")
    annotation: str = Field(description="The feedback or comment")
    severity: str = Field(description="One of: error, warning, suggestion")


class DocumentEvaluation(BaseModel):
    """Evaluation result for a document."""
    score: float = Field(description="Score from 1 to 10", ge=1, le=10)
    summary: str = Field(description="Overall evaluation summary")
    strengths: List[str] = Field(description="List of document strengths")
    weaknesses: List[str] = Field(description="List of areas needing improvement")
    annotations: List[DocumentAnnotation] = Field(description="Specific annotations")
    recommendations: List[str] = Field(description="Actionable recommendations")


class GeminiService:
    """Service class for Gemini AI operations."""

    def __init__(self, language: str = "et"):
        """
        Initialize Gemini service.

        Args:
            language: Language for responses ('et' or 'en')
        """
        self.client = get_gemini_client()
        self.model = "gemini-2.0-flash"
        self.language = language

    def _get_language_instruction(self) -> str:
        """Get instruction for response language."""
        if self.language == "et":
            return "Respond in Estonian (eesti keeles). All text should be in Estonian."
        return "Respond in English. All text should be in English."

    def extract_requirements(self, document_text: str) -> Optional[ExtractedRequirements]:
        """
        Extract requirements checklist from grant documentation.

        Args:
            document_text: Text content of the grant requirements document

        Returns:
            ExtractedRequirements object or None on error
        """
        prompt = f"""
        {self._get_language_instruction()}

        You are an expert at analyzing grant application requirements.
        Analyze the following grant documentation and extract a comprehensive checklist
        of ALL requirements that applicants must fulfill.

        For each requirement:
        1. Give it a clear, concise name
        2. Provide a detailed description of what is needed
        3. Indicate if it's mandatory or optional

        Be thorough - include all requirements mentioned in the document, including:
        - Required documents
        - Eligibility criteria
        - Financial requirements
        - Technical requirements
        - Timeline/deadline requirements
        - Reporting requirements

        Document text:
        ---
        {document_text[:15000]}
        ---

        Extract all requirements as a structured checklist.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedRequirements,
                    temperature=0.3
                )
            )

            return ExtractedRequirements.model_validate_json(response.text)
        except Exception as e:
            print(f"Error extracting requirements: {e}")
            return None

    def evaluate_document(
        self,
        document_text: str,
        requirements_text: str,
        document_name: str
    ) -> Optional[DocumentEvaluation]:
        """
        Evaluate a user's document against grant requirements.

        Args:
            document_text: Text content of the document to evaluate
            requirements_text: Text of grant requirements
            document_name: Name of the document being evaluated

        Returns:
            DocumentEvaluation object or None on error
        """
        prompt = f"""
        {self._get_language_instruction()}

        You are an expert grant application evaluator.
        Evaluate the following document against the grant requirements.

        Provide:
        1. An overall score from 1-10 (10 being perfect)
        2. A brief summary of the evaluation
        3. List of strengths (what the document does well)
        4. List of weaknesses (areas needing improvement)
        5. Specific annotations pointing to problematic text segments
        6. Actionable recommendations for improvement

        Be constructive but thorough. The goal is to help the applicant improve.

        GRANT REQUIREMENTS:
        ---
        {requirements_text[:5000]}
        ---

        DOCUMENT TO EVALUATE ({document_name}):
        ---
        {document_text[:10000]}
        ---

        Evaluate this document comprehensively.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DocumentEvaluation,
                    temperature=0.4
                )
            )

            return DocumentEvaluation.model_validate_json(response.text)
        except Exception as e:
            print(f"Error evaluating document: {e}")
            return None

    def generate_content(
        self,
        project_info: dict,
        documents_text: dict,
        requirements_text: str,
        content_type: str
    ) -> Optional[str]:
        """
        Generate application content based on project documents.

        Args:
            project_info: Project metadata (name, description)
            documents_text: Dict of document name -> extracted text
            requirements_text: Grant requirements text
            content_type: Type of content to generate ('narrative', 'budget', 'summary')

        Returns:
            Generated content string or None on error
        """
        docs_summary = "\n\n".join([
            f"=== {name} ===\n{text[:3000]}"
            for name, text in documents_text.items()
        ])

        prompts = {
            "narrative": f"""
            {self._get_language_instruction()}

            You are an expert grant writer. Based on the project information and uploaded documents,
            write a professional project narrative for a grant application.

            The narrative should:
            - Clearly describe the project goals and objectives
            - Explain the methodology and approach
            - Highlight the expected outcomes and impact
            - Address all relevant requirements from the grant

            PROJECT: {project_info.get('name', '')}
            DESCRIPTION: {project_info.get('description', '')}

            GRANT REQUIREMENTS:
            {requirements_text[:3000]}

            SOURCE DOCUMENTS:
            {docs_summary[:8000]}

            Write a compelling, professional project narrative.
            """,

            "summary": f"""
            {self._get_language_instruction()}

            Write a concise executive summary for the following grant application.
            The summary should be 1-2 paragraphs and capture the essence of the project.

            PROJECT: {project_info.get('name', '')}
            DESCRIPTION: {project_info.get('description', '')}

            SOURCE DOCUMENTS:
            {docs_summary[:5000]}

            Write a clear, professional executive summary.
            """,

            "budget": f"""
            {self._get_language_instruction()}

            Based on the project information, suggest a budget breakdown for this grant application.
            Include typical cost categories like:
            - Personnel costs
            - Equipment and materials
            - Travel and meetings
            - Subcontracting
            - Other direct costs
            - Overhead/indirect costs

            PROJECT: {project_info.get('name', '')}
            DESCRIPTION: {project_info.get('description', '')}

            SOURCE DOCUMENTS:
            {docs_summary[:5000]}

            Provide a reasonable budget breakdown with estimated amounts and justifications.
            Format as a table with columns: Category, Description, Amount (EUR), Justification
            """
        }

        prompt = prompts.get(content_type, prompts["narrative"])

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=4000
                )
            )

            return response.text
        except Exception as e:
            print(f"Error generating content: {e}")
            return None
