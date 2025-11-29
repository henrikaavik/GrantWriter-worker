"""Extract and process grant requirements."""

from typing import Optional
from .gemini_client import GeminiService, ExtractedRequirements
from .document_parser import DocumentParser
from src.database.grants import update_grant_requirement
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
