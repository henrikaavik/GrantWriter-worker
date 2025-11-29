"""Supabase database connection utilities (worker version - no streamlit)."""

from supabase import create_client, Client
from typing import Optional
from ..utils.secrets import get_supabase_url, get_supabase_key

# Module-level client cache
_db_client: Optional[Client] = None


def get_db() -> Client:
    """
    Get Supabase database client.

    Returns:
        Supabase client instance
    """
    global _db_client

    if _db_client is None:
        url = get_supabase_url()
        key = get_supabase_key()
        _db_client = create_client(url, key)

    return _db_client


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
