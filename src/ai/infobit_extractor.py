"""Infobit extractor - extracts values from documents to fill infobit fields."""

from typing import List, Dict, Any, Optional
from google.genai import types
from .gemini_client import get_gemini_client
from .models import DocumentExtraction, ExtractedInfobitValue
from .document_parser import parse_document


def extract_infobits_from_document(
    file_data: bytes,
    file_name: str,
    empty_infobits: List[Dict[str, Any]],
    language: str = "et"
) -> Optional[DocumentExtraction]:
    """
    Extract values from a document and map to empty infobit fields.

    Args:
        file_data: Raw file bytes
        file_name: Name of the file
        empty_infobits: List of infobit records that need to be filled
        language: Language for extraction ('et' or 'en')

    Returns:
        DocumentExtraction object or None on error
    """
    if not empty_infobits:
        return None

    # Parse document to extract text
    try:
        document_text = parse_document(file_data, file_name)
        if not document_text:
            print(f"Failed to extract text from {file_name}")
            return None
    except Exception as e:
        print(f"Error parsing document: {e}")
        return None

    # Build field descriptions for AI
    fields_description = ""
    for infobit in empty_infobits:
        field_name = infobit.get("field_name", "")
        field_label = infobit.get("field_label", "")
        field_desc = infobit.get("field_description", "")
        fields_description += f"- {field_name}: {field_label} - {field_desc}\n"

    # Call AI to extract and map values
    client = get_gemini_client()
    model = "gemini-2.0-flash"

    lang_instruction = (
        "The document is likely in Estonian. Extract values in their original language."
        if language == "et"
        else "Extract values in their original language from the document."
    )

    prompt = f"""
    {lang_instruction}

    You are an expert at extracting structured information from documents.
    Analyze the following document and extract values that match the specified fields.

    For each field you can find relevant information for:
    1. Extract the exact value from the document
    2. Provide a confidence score (0.0-1.0) based on how certain you are
    3. Include the source text snippet (max 100 chars)

    Only extract values you are confident about. Don't guess or make up information.
    If you cannot find information for a field, skip it entirely.

    FIELDS TO EXTRACT:
    ---
    {fields_description}
    ---

    DOCUMENT CONTENT:
    ---
    {document_text[:15000]}
    ---

    Extract matching values from the document for as many fields as possible.
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DocumentExtraction,
                temperature=0.2
            )
        )

        return DocumentExtraction.model_validate_json(response.text)
    except Exception as e:
        print(f"Error extracting infobits: {e}")
        return None


def extract_text_from_file(file_data: bytes, file_name: str) -> str:
    """
    Extract text from a file using Docling.

    Args:
        file_data: Raw file bytes
        file_name: Name of the file

    Returns:
        Extracted text content
    """
    try:
        return parse_document(file_data, file_name)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
