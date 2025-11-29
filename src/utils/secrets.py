"""Secrets management - supports both st.secrets and environment variables."""

import os
import streamlit as st


def get_secret(key: str, subkey: str = None) -> str:
    """
    Get a secret value from st.secrets or environment variables.

    Supports both formats:
    - st.secrets["supabase"]["url"] -> get_secret("supabase", "url")
    - os.environ["SUPABASE_URL"] -> get_secret("supabase", "url")

    Args:
        key: Top-level key (e.g., "supabase", "google")
        subkey: Sub-key (e.g., "url", "key", "gemini_api_key")

    Returns:
        Secret value

    Raises:
        KeyError: If secret not found
    """
    # Try st.secrets first
    try:
        if subkey:
            return st.secrets[key][subkey]
        return st.secrets[key]
    except Exception:
        # Catches KeyError, FileNotFoundError, and any other secrets-related errors
        pass

    # Fall back to environment variables
    # Convert to uppercase ENV var format: supabase.url -> SUPABASE_URL
    if subkey:
        env_key = f"{key.upper()}_{subkey.upper()}"
    else:
        env_key = key.upper()

    # Handle special mappings
    env_mappings = {
        "GOOGLE_GEMINI_API_KEY": "GEMINI_API_KEY",
    }
    env_key = env_mappings.get(env_key, env_key)

    value = os.environ.get(env_key)
    if value:
        return value

    raise KeyError(f"Secret not found: {key}.{subkey} or {env_key}")


def get_supabase_url() -> str:
    """Get Supabase URL."""
    return get_secret("supabase", "url")


def get_supabase_key() -> str:
    """Get Supabase anon key."""
    return get_secret("supabase", "key")


def get_gemini_api_key() -> str:
    """Get Gemini API key."""
    return get_secret("google", "gemini_api_key")
