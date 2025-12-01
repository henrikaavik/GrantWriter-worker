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

    prompt = f"""
    TÄHTIS: Kogu väljund PEAB olema eesti keeles.
    Kui dokument on inglise keeles või muus keeles, tõlgi eraldatud väärtused eesti keelde.

    Sa oled ekspert struktureeritud info eraldamisel dokumentidest.
    Analüüsi järgmist dokumenti ja eralda väärtused, mis vastavad määratud väljadele.

    KRIITILISED REEGLID:
    1. ETTEVÕTTE KIRJELDUS (company_description) peab olema ETTEVÕTTE/ORGANISATSIOONI kohta, MITTE üksikisiku CV või kirjeldus
    2. Ära sega isiklikke andmeid (CV, haridus, töökogemus) ettevõtte väljadega
    3. CV-d on TUGIDOKUMENDID - neist EI TOHI eraldada ettevõtte infot
    4. Äriplaanist eralda ettevõtte info, mitte asutaja isiklik kirjeldus
    5. Mitte kõik dokumendid sisaldavad eraldatavat infot - SEE ON NORMAALNE

    MIDA MITTE TEHA:
    - Ära pane CV teksti ettevõtte kirjeldusse
    - Ära pane isiklikku haridust ettevõtte andmetesse
    - Ära sega "Full Stack Developer" tüüpi teksti ettevõtte kirjeldusse
    - Ära sunni infot väljadesse kui see ei sobi - JÄTA VAHELE

    Iga välja kohta, mille kohta leiad SOBIVAT infot:
    1. Eralda väärtus dokumendist (EESTI KEELES, tõlgi vajadusel)
    2. Anna usaldusväärsuse hinne (0.0-1.0)
    3. Lisa lähteteksti väljavõte (max 100 tähemärki)

    Eralda ainult väärtusi, milles oled kindel JA mis on õige tüüpi info selle välja jaoks.
    Kui ei leia välja kohta SOBIVAT infot, jäta see vahele.

    VÄLJAD, MIDA ERALDADA:
    ---
    {fields_description}
    ---

    DOKUMENDI SISU:
    ---
    {document_text[:15000]}
    ---

    Eralda dokumentidest sobivad väärtused nii paljude väljade jaoks kui võimalik.
    KÕIK ERALDATUD VÄÄRTUSED PEAVAD OLEMA EESTI KEELES.
    OLE ETTEVAATLIK: Kontrolli, et iga väärtus sobib välja tüübiga!
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
