"""Supabase storage operations."""

import streamlit as st
from supabase import create_client, Client
from typing import Tuple, Optional
import uuid
import re
import unicodedata


def get_storage_client() -> Client:
    """Get Supabase client for storage operations - uses authenticated client if available."""
    # Use the authenticated client from auth module if it exists
    if "supabase_client" in st.session_state:
        return st.session_state.supabase_client
    # Fallback to creating a new client
    if "storage_client" not in st.session_state:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        st.session_state.storage_client = create_client(url, key)
    return st.session_state.storage_client


def upload_file(
    bucket_id: str,
    file_data: bytes,
    file_path: str,
    content_type: str = "application/octet-stream"
) -> Optional[str]:
    """
    Upload a file to Supabase storage.

    Args:
        bucket_id: Storage bucket name
        file_data: File content as bytes
        file_path: Destination path in bucket
        content_type: MIME type of the file

    Returns:
        File path if successful, None otherwise
    """
    client = get_storage_client()
    client.storage.from_(bucket_id).upload(
        path=file_path,
        file=file_data,
        file_options={"content-type": content_type}
    )
    return file_path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for storage - remove special characters and spaces.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for storage
    """
    # Normalize unicode characters (convert ö to o, etc.)
    normalized = unicodedata.normalize('NFKD', filename)
    ascii_filename = normalized.encode('ascii', 'ignore').decode('ascii')

    # Replace spaces with underscores
    ascii_filename = ascii_filename.replace(' ', '_')

    # Remove any remaining invalid characters (keep alphanumeric, underscore, hyphen, dot)
    safe_filename = re.sub(r'[^a-zA-Z0-9_\-.]', '', ascii_filename)

    # Ensure we have at least something
    if not safe_filename or safe_filename == '.':
        safe_filename = 'file'

    return safe_filename


def upload_requirement_doc(
    grant_id: str,
    file_data: bytes,
    filename: str,
    content_type: str = "application/pdf"
) -> Optional[str]:
    """
    Upload a grant requirement document (admin only).

    Args:
        grant_id: Grant UUID
        file_data: File content as bytes
        filename: Original filename
        content_type: MIME type

    Returns:
        File path if successful, None otherwise
    """
    safe_filename = sanitize_filename(filename)
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = f"{grant_id}/{unique_filename}"
    return upload_file("grant-requirements", file_data, file_path, content_type)


def upload_project_doc(
    user_id: str,
    project_id: str,
    file_data: bytes,
    filename: str,
    content_type: str = "application/pdf"
) -> Optional[str]:
    """
    Upload a project document.

    Args:
        user_id: User UUID
        project_id: Project UUID
        file_data: File content as bytes
        filename: Original filename
        content_type: MIME type

    Returns:
        File path if successful, None otherwise
    """
    safe_filename = sanitize_filename(filename)
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = f"{user_id}/{project_id}/{unique_filename}"
    return upload_file("project-documents", file_data, file_path, content_type)


def download_file(bucket_id: str, file_path: str) -> Optional[bytes]:
    """
    Download a file from Supabase storage.

    Args:
        bucket_id: Storage bucket name
        file_path: File path in bucket

    Returns:
        File content as bytes or None
    """
    try:
        client = get_storage_client()
        response = client.storage.from_(bucket_id).download(file_path)
        return response
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None


def delete_file(bucket_id: str, file_path: str) -> bool:
    """
    Delete a file from Supabase storage.

    Args:
        bucket_id: Storage bucket name
        file_path: File path in bucket

    Returns:
        True if successful
    """
    try:
        client = get_storage_client()
        client.storage.from_(bucket_id).remove([file_path])
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def get_public_url(bucket_id: str, file_path: str) -> Optional[str]:
    """
    Get public URL for a file (for public buckets).

    Args:
        bucket_id: Storage bucket name
        file_path: File path in bucket

    Returns:
        Public URL or None
    """
    try:
        client = get_storage_client()
        response = client.storage.from_(bucket_id).get_public_url(file_path)
        return response
    except Exception as e:
        print(f"Error getting public URL: {e}")
        return None


def get_signed_url(bucket_id: str, file_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Get a signed URL for temporary access to a private file.

    Args:
        bucket_id: Storage bucket name
        file_path: File path in bucket
        expires_in: URL expiration time in seconds (default 1 hour)

    Returns:
        Signed URL or None
    """
    try:
        client = get_storage_client()
        response = client.storage.from_(bucket_id).create_signed_url(
            file_path, expires_in
        )
        return response.get("signedURL")
    except Exception as e:
        print(f"Error creating signed URL: {e}")
        return None


def get_mime_type(filename: str) -> str:
    """
    Get MIME type based on file extension.

    Args:
        filename: Filename with extension

    Returns:
        MIME type string
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    mime_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "txt": "text/plain",
        "csv": "text/csv",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg"
    }
    return mime_types.get(ext, "application/octet-stream")
