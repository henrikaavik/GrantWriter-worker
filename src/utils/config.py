"""Application configuration constants."""

APP_VERSION = "0.5.0"
APP_NAME = "GrantWriter"

# Supported languages
SUPPORTED_LANGUAGES = ["et", "en"]
DEFAULT_LANGUAGE = "et"

# File upload settings
MAX_FILE_SIZE_MB = 50
ALLOWED_DOCUMENT_TYPES = ["pdf", "docx", "xlsx", "doc", "xls"]

# Project statuses
PROJECT_STATUSES = ["draft", "in_progress", "submitted", "completed"]

# User roles (pending = awaiting approval, user = approved, admin = full access)
USER_ROLES = ["pending", "user", "admin"]
