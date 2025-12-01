"""Extract and process grant requirements."""

from typing import Optional, List, Dict, Any
from .gemini_client import GeminiService, ExtractedRequirements, ExtractedOutputDocuments
from .document_parser import DocumentParser
from src.database.grants import update_grant_requirement, bulk_create_grant_output_documents
from src.storage.supabase_storage import download_file


class RequirementsExtractor:
    """Extract and process grant requirements from documents."""

    def __init__(self, language: str = "et"):
        """
        Initialize requirements extractor.

        Args:
            language: Language for AI responses ('et' or 'en')
        """
        self.gemini = GeminiService(language)
        self.parser = DocumentParser()

    def process_requirement_document(
        self,
        requirement_id: str,
        file_path: str
    ) -> Optional[ExtractedRequirements]:
        """
        Process a grant requirement document and extract checklist.

        Args:
            requirement_id: ID of the grant_requirement record
            file_path: Path to file in storage bucket

        Returns:
            Extracted requirements or None on error
        """
        # Download file from storage
        file_data = download_file("grant-requirements", file_path)
        if not file_data:
            print(f"Could not download file: {file_path}")
            return None

        # Get filename from path
        filename = file_path.split("/")[-1]

        # Parse document to extract text
        parsed = self.parser.parse_document(file_data, filename)
        text = parsed.get("text", "")

        if not text:
            print(f"Could not extract text from: {filename}")
            return None

        # Extract requirements using AI
        requirements = self.gemini.extract_requirements(text)

        if requirements:
            # Save extracted checklist to database
            checklist_data = [item.model_dump() for item in requirements.checklist]
            update_grant_requirement(
                requirement_id,
                extracted_checklist=checklist_data
            )

        return requirements

    def extract_from_text(self, text: str) -> Optional[ExtractedRequirements]:
        """
        Extract requirements from plain text.

        Args:
            text: Text content to analyze

        Returns:
            Extracted requirements or None on error
        """
        return self.gemini.extract_requirements(text)

    def extract_output_documents(
        self,
        grant_id: str,
        file_path: str
    ) -> Optional[ExtractedOutputDocuments]:
        """
        Extract output documents from a grant requirement document.

        Args:
            grant_id: ID of the grant
            file_path: Path to file in storage bucket

        Returns:
            ExtractedOutputDocuments or None on error
        """
        # Download file from storage
        file_data = download_file("grant-requirements", file_path)
        if not file_data:
            print(f"Could not download file: {file_path}")
            return None

        # Get filename from path
        filename = file_path.split("/")[-1]

        # Parse document to extract text
        parsed = self.parser.parse_document(file_data, filename)
        text = parsed.get("text", "")

        if not text:
            print(f"Could not extract text from: {filename}")
            return None

        # Extract output documents using AI
        output_docs = self.gemini.extract_output_documents(text)

        if output_docs and output_docs.documents:
            # Save to database
            docs_data = []
            for i, doc in enumerate(output_docs.documents):
                doc_data = {
                    "name": doc.name,
                    "name_en": doc.name_en,
                    "description": doc.description,
                    "description_en": doc.description_en,
                    "document_type": doc.document_type,
                    "is_required": doc.is_required,
                    "sort_order": i,
                    "fields": [f.model_dump() for f in doc.fields] if doc.fields else []
                }
                docs_data.append(doc_data)

            bulk_create_grant_output_documents(grant_id, docs_data)

        return output_docs

    def extract_output_documents_from_text(
        self,
        text: str
    ) -> Optional[ExtractedOutputDocuments]:
        """
        Extract output documents from plain text.

        Args:
            text: Text content to analyze

        Returns:
            ExtractedOutputDocuments or None on error
        """
        return self.gemini.extract_output_documents(text)
