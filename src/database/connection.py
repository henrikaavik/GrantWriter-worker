"""Supabase database connection utilities."""

import streamlit as st
from supabase import create_client, Client
from typing import Optional
from ..utils.secrets import get_supabase_url, get_supabase_key


def get_db() -> Client:
    """
    Get Supabase database client.
    Uses authenticated client if available for proper RLS access.

    Returns:
        Supabase client instance
    """
    # Prefer the authenticated client from auth module
    if "supabase_client" in st.session_state:
        return st.session_state.supabase_client

    # Fallback to creating a new client
    if "db_client" not in st.session_state:
        url = get_supabase_url()
        key = get_supabase_key()
        st.session_state.db_client = create_client(url, key)
    return st.session_state.db_client


def execute_query(query, ttl: Optional[str] = None):
    """
    Execute a database query.

    Args:
        query: Supabase query builder
        ttl: Cache TTL (not used currently, for future caching)

    Returns:
        Query result
    """
    return query.execute()
