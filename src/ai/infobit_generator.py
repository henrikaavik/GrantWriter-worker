"""Infobit generator - generates required fields from grant requirements and examples."""

from typing import List, Dict, Any, Optional
from google.genai import types
from .gemini_client import get_gemini_client
from .models import GeneratedInfobits, InfobitDefinition
from ..database.grants import get_grant_requirements, get_grant_examples


def generate_infobits_for_grant(grant_id: str, language: str = "et") -> Optional[GeneratedInfobits]:
    """
    Generate infobits (required information fields) for a grant.

    Args:
        grant_id: Grant UUID
        language: Language for responses ('et' or 'en')

    Returns:
        GeneratedInfobits object or None on error
    """
    # Fetch grant requirements
    requirements = get_grant_requirements(grant_id)
    requirements_text = ""
    for req in requirements:
        checklist = req.get("extracted_checklist", {})
        if isinstance(checklist, dict):
            items = checklist.get("checklist", [])
            for item in items:
                requirements_text += f"- {item.get('name', '')}: {item.get('description', '')}\n"
        requirements_text += f"\nDocument: {req.get('name', '')}\n"

    # Fetch example documents
    examples = get_grant_examples(grant_id)
    examples_text = ""
    for ex in examples:
        extracted = ex.get("extracted_text", "")
        if extracted:
            examples_text += f"\n=== Example: {ex.get('name', '')} ===\n{extracted[:3000]}\n"

    if not requirements_text and not examples_text:
        return None

    # Generate infobits using AI
    client = get_gemini_client()
    model = "gemini-2.0-flash"

    lang_instruction = (
        "Respond in Estonian (eesti keeles). All labels and descriptions should be in Estonian."
        if language == "et"
        else "Respond in English. All labels and descriptions should be in English."
    )

    prompt = f"""
    {lang_instruction}

    You are an expert at analyzing grant applications. Based on the grant requirements
    and example documents below, identify ALL the information fields (infobits) that
    an applicant needs to provide to complete their application.

    For each infobit, provide:
    1. field_name: A machine-readable identifier (snake_case, e.g., "company_name")
    2. field_label: Human-readable label in Estonian
    3. field_label_en: Human-readable label in English
    4. field_description: Help text explaining what information is needed
    5. category: One of: general, company, project, budget, team, timeline, outcomes
    6. is_required: Whether this field is mandatory (true/false)
    7. sort_order: Display order within category (start from 1)

    Categories should be used as follows:
    - general: Basic project information (name, summary, etc.)
    - company: Organization/company details
    - project: Project specifics, goals, methodology
    - budget: Financial information
    - team: Team members, roles, qualifications
    - timeline: Schedule, milestones, deadlines
    - outcomes: Expected results, impact, KPIs

    GRANT REQUIREMENTS:
    ---
    {requirements_text[:8000]}
    ---

    EXAMPLE APPLICATION DOCUMENTS (for reference):
    ---
    {examples_text[:8000]}
    ---

    Generate a comprehensive list of all information fields needed for this grant application.
    Be thorough - include all fields that would be needed based on the requirements and examples.
    Typical fields include: company name, registration number, contact person, project title,
    project summary, objectives, methodology, budget breakdown, team members, timeline, etc.
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeneratedInfobits,
                temperature=0.3
            )
        )

        return GeneratedInfobits.model_validate_json(response.text)
    except Exception as e:
        print(f"Error generating infobits: {e}")
        return None


def get_default_infobits(language: str = "et") -> List[Dict[str, Any]]:
    """
    Get default infobits when AI generation fails.

    Args:
        language: Language for labels

    Returns:
        List of default infobit definitions
    """
    defaults = [
        {
            "field_name": "company_name",
            "field_label": "Ettevõtte nimi" if language == "et" else "Company Name",
            "field_label_en": "Company Name",
            "field_description": "Taotleja ettevõtte täielik nimi" if language == "et" else "Full legal name of the applying company",
            "category": "company",
            "is_required": True,
            "sort_order": 1
        },
        {
            "field_name": "registration_number",
            "field_label": "Registrikood" if language == "et" else "Registration Number",
            "field_label_en": "Registration Number",
            "field_description": "Äriregistri kood" if language == "et" else "Business registry code",
            "category": "company",
            "is_required": True,
            "sort_order": 2
        },
        {
            "field_name": "contact_person",
            "field_label": "Kontaktisik" if language == "et" else "Contact Person",
            "field_label_en": "Contact Person",
            "field_description": "Projekti kontaktisiku nimi" if language == "et" else "Name of the project contact person",
            "category": "company",
            "is_required": True,
            "sort_order": 3
        },
        {
            "field_name": "contact_email",
            "field_label": "E-post" if language == "et" else "Email",
            "field_label_en": "Email",
            "field_description": "Kontaktisiku e-posti aadress" if language == "et" else "Contact person's email address",
            "category": "company",
            "is_required": True,
            "sort_order": 4
        },
        {
            "field_name": "project_title",
            "field_label": "Projekti pealkiri" if language == "et" else "Project Title",
            "field_label_en": "Project Title",
            "field_description": "Projekti lühike ja tabav pealkiri" if language == "et" else "Short and descriptive project title",
            "category": "general",
            "is_required": True,
            "sort_order": 1
        },
        {
            "field_name": "project_summary",
            "field_label": "Projekti kokkuvõte" if language == "et" else "Project Summary",
            "field_label_en": "Project Summary",
            "field_description": "Projekti lühikokkuvõte (1-2 lõiku)" if language == "et" else "Brief project summary (1-2 paragraphs)",
            "category": "general",
            "is_required": True,
            "sort_order": 2
        },
        {
            "field_name": "project_objectives",
            "field_label": "Projekti eesmärgid" if language == "et" else "Project Objectives",
            "field_label_en": "Project Objectives",
            "field_description": "Projekti peamised eesmärgid ja oodatavad tulemused" if language == "et" else "Main project objectives and expected outcomes",
            "category": "project",
            "is_required": True,
            "sort_order": 1
        },
        {
            "field_name": "methodology",
            "field_label": "Metoodika" if language == "et" else "Methodology",
            "field_label_en": "Methodology",
            "field_description": "Projekti läbiviimise metoodika ja tegevused" if language == "et" else "Project methodology and activities",
            "category": "project",
            "is_required": True,
            "sort_order": 2
        },
        {
            "field_name": "total_budget",
            "field_label": "Kogueelarve" if language == "et" else "Total Budget",
            "field_label_en": "Total Budget",
            "field_description": "Projekti kogueelarve eurodes" if language == "et" else "Total project budget in EUR",
            "category": "budget",
            "is_required": True,
            "sort_order": 1
        },
        {
            "field_name": "requested_funding",
            "field_label": "Taotletav toetus" if language == "et" else "Requested Funding",
            "field_label_en": "Requested Funding",
            "field_description": "Toetusena taotletav summa eurodes" if language == "et" else "Amount requested as grant in EUR",
            "category": "budget",
            "is_required": True,
            "sort_order": 2
        },
        {
            "field_name": "project_duration",
            "field_label": "Projekti kestus" if language == "et" else "Project Duration",
            "field_label_en": "Project Duration",
            "field_description": "Projekti kestus kuudes" if language == "et" else "Project duration in months",
            "category": "timeline",
            "is_required": True,
            "sort_order": 1
        },
        {
            "field_name": "start_date",
            "field_label": "Alguskuupäev" if language == "et" else "Start Date",
            "field_label_en": "Start Date",
            "field_description": "Projekti planeeritud alguskuupäev" if language == "et" else "Planned project start date",
            "category": "timeline",
            "is_required": False,
            "sort_order": 2
        },
        {
            "field_name": "expected_outcomes",
            "field_label": "Oodatavad tulemused" if language == "et" else "Expected Outcomes",
            "field_label_en": "Expected Outcomes",
            "field_description": "Projekti oodatavad tulemused ja mõju" if language == "et" else "Expected project results and impact",
            "category": "outcomes",
            "is_required": True,
            "sort_order": 1
        },
    ]

    return defaults
