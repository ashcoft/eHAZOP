"""Core module containing configuration, database, security, and utilities."""

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db, init_db, close_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from app.core.dependencies import (
    CurrentUser,
    StudyAccess,
    get_current_user,
    require_admin,
    require_facilitator,
    require_participant,
    require_scribe,
    require_study_access,
    require_viewer,
)
from app.core.websocket import ConnectionManager, manager
from app.core.audit import AuditLog, create_audit_entry

__all__ = [
    "Settings",
    "get_settings",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_password_hash",
    "verify_access_token",
    "verify_password",
    "verify_refresh_token",
    "CurrentUser",
    "StudyAccess",
    "get_current_user",
    "require_admin",
    "require_facilitator",
    "require_participant",
    "require_scribe",
    "require_study_access",
    "require_viewer",
    "ConnectionManager",
    "manager",
    "AuditLog",
    "create_audit_entry",
]