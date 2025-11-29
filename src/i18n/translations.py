"""Internationalization (i18n) utilities (worker version - no streamlit)."""

import json
from pathlib import Path
from typing import Any, Dict
from functools import lru_cache

# Path to locale files
LOCALES_PATH = Path(__file__).parent / "locales"

# Module-level language setting (default Estonian)
_current_language = "et"


@lru_cache(maxsize=2)
def load_translations(language: str) -> dict:
    """
    Load translations for a language.

    Args:
        language: Language code ('et' or 'en')

    Returns:
        Dictionary of translations
    """
    file_path = LOCALES_PATH / f"{language}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fall back to Estonian if file not found
        with open(LOCALES_PATH / "et.json", "r", encoding="utf-8") as f:
            return json.load(f)


def get_language() -> str:
    """
    Get current language.

    Returns:
        Language code ('et' or 'en')
    """
    return _current_language


def set_language(language: str):
    """
    Set current language.

    Args:
        language: Language code ('et' or 'en')
    """
    global _current_language
    if language in ["et", "en"]:
        _current_language = language


def t(key: str, **kwargs) -> str:
    """
    Get translation for a key.

    Args:
        key: Translation key (supports dot notation for nested keys)
        **kwargs: Variables for string formatting

    Returns:
        Translated string or the key itself if not found
    """
    language = get_language()
    translations = load_translations(language)

    # Support nested keys with dot notation
    value: Any = translations
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
            if value is None:
                return key
        else:
            return key

    if not isinstance(value, str):
        return key

    # Apply variable substitution if kwargs provided
    if kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value

    return value


def get_localized_field(data: dict, field: str, language: str = None) -> str:
    """
    Get localized field from a database record.
    Falls back to base field if localized version not available.

    Args:
        data: Database record dict
        field: Base field name (e.g., 'name', 'description')
        language: Optional language override

    Returns:
        Localized value or base value
    """
    lang = language or get_language()

    if lang == "en":
        localized_key = f"{field}_en"
        if localized_key in data and data[localized_key]:
            return data[localized_key]

    return data.get(field, "")
