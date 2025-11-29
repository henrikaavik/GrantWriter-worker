"""Supabase authentication utilities."""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
from ..utils.secrets import get_supabase_url, get_supabase_key


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    if "supabase_client" not in st.session_state:
        url = get_supabase_url()
        key = get_supabase_key()
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def init_session_state():
    """Initialize authentication-related session state."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False


def sign_up(email: str, password: str, full_name: str = "") -> Dict[str, Any]:
    """
    Register a new user.

    Args:
        email: User's email address
        password: User's password
        full_name: User's full name (optional)

    Returns:
        Dict with success status and user data or error
    """
    try:
        client = get_supabase_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })

        if response.user:
            return {
                "success": True,
                "user": response.user,
                "message": "Registration successful. Please check your email to verify your account."
            }
        else:
            return {
                "success": False,
                "error": "Registration failed"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def sign_in(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in an existing user.

    Args:
        email: User's email address
        password: User's password

    Returns:
        Dict with success status and user/session data or error
    """
    try:
        client = get_supabase_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            # Store user in session state
            st.session_state.user = {
                "id": str(response.user.id),
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name", "")
            }
            st.session_state.authenticated = True

            # Fetch profile for role info - use same client which now has auth token
            try:
                profile_response = client.table("profiles").select("*").eq("id", str(response.user.id)).single().execute()
                if profile_response.data:
                    st.session_state.profile = profile_response.data
                    st.session_state.user["role"] = profile_response.data.get("role", "pending")
                    st.session_state.user["full_name"] = profile_response.data.get("full_name", "")
            except Exception:
                # If profile fetch fails, default to pending role
                st.session_state.user["role"] = "pending"

            return {
                "success": True,
                "user": st.session_state.user
            }
        else:
            return {
                "success": False,
                "error": "Login failed"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def sign_out():
    """Sign out the current user."""
    try:
        client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        pass
    finally:
        # Clear session state
        st.session_state.user = None
        st.session_state.profile = None
        st.session_state.authenticated = False
        # Clear other session data
        keys_to_remove = ["selected_grant", "selected_project"]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from database.

    Args:
        user_id: The user's UUID

    Returns:
        Profile dict or None
    """
    try:
        client = get_supabase_client()
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()
        print(f"DEBUG: Profile fetch for {user_id}: {response.data}")
        return response.data
    except Exception as e:
        print(f"DEBUG: Profile fetch error for {user_id}: {e}")
        return None


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the currently authenticated user.

    Returns:
        User dict or None if not authenticated
    """
    init_session_state()
    return st.session_state.user if st.session_state.authenticated else None


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    init_session_state()
    return st.session_state.authenticated and st.session_state.user is not None


def is_admin() -> bool:
    """Check if current user is admin."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "admin"


def is_pending() -> bool:
    """Check if current user is pending approval."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "pending"


def is_approved() -> bool:
    """Check if current user is approved (user or admin role)."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") in ["user", "admin"]


def require_auth():
    """
    Require authentication to access a page.
    Shows warning and stops execution if not authenticated or pending approval.
    """
    from src.i18n.translations import t

    init_session_state()
    if not is_authenticated():
        st.warning(t("auth.login_required"))
        st.info(t("auth.go_to_home"))
        st.stop()

    # Check if user is pending approval
    if is_pending():
        st.warning(t("auth.pending_approval"))
        st.info(t("auth.pending_message"))
        st.stop()


def require_admin():
    """
    Require admin role to access a page.
    Shows error and stops execution if not admin.
    """
    from src.i18n.translations import t

    require_auth()
    if not is_admin():
        st.error(t("auth.admin_required"))
        st.stop()


def update_user_language(language: str):
    """Update user's preferred language in profile."""
    user = get_current_user()
    if not user:
        return

    try:
        client = get_supabase_client()
        client.table("profiles").update({
            "preferred_language": language
        }).eq("id", user["id"]).execute()
    except Exception:
        pass
