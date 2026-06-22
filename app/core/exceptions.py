"""
Custom exception hierarchy for the Task Management API.

Design rationale:
- Service layer raises Python exceptions (not HTTPExceptions) so it remains
  interface-agnostic — the same service can be called from a REST API, CLI,
  Celery task, or test without importing FastAPI.
- The API layer (main.py) maps each exception type to the correct HTTP status.
"""


class AppBaseException(Exception):
    """Base exception for all application-level errors."""
    pass


# ── User exceptions ────────────────────────────────────────────────────────
class UserAlreadyExistsException(AppBaseException):
    """Raised when attempting to register a username that is already taken."""
    pass


class UserNotFoundException(AppBaseException):
    """Raised when a requested user does not exist in the database."""
    pass


# ── Task exceptions ────────────────────────────────────────────────────────
class TaskNotFoundException(AppBaseException):
    """Raised when a requested task does not exist in the database."""
    pass


# ── Project exceptions ─────────────────────────────────────────────────────
class ProjectNotFoundException(AppBaseException):
    """Raised when a requested project does not exist in the database."""
    pass


class MemberAdditionError(AppBaseException):
    """Raised when adding a member to a project fails (e.g. already a member)."""
    pass


class MemberRemovalError(AppBaseException):
    """Raised when removing a member from a project fails (e.g. not a member)."""
    pass


# ── Authorization exceptions ───────────────────────────────────────────────
class PermissionDeniedException(AppBaseException):
    """Raised when a user attempts an action they are not authorized to perform."""
    pass
