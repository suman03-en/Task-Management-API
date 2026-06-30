import uuid
from typing import cast
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.users import get_current_user
from app.dependencies.db import get_db
from app.models.project import ProjectMember
from app.models.task import Task
from app.models.user import User as UserModel
from app.core.exceptions import PermissionDeniedException, TaskNotFoundException


PROJECT_ROLE_PERMISSIONS = {
    "creator": {
        ("read", "project"),
        ("create", "task"),
        ("read", "task"),
        ("update", "task"),
        ("delete", "task"),
        ("add_member", "project"),
        ("remove_member", "project"),
        ("update", "project"),
        ("delete", "project"),
    },

    "member": {
        ("read", "project"),
        ("read", "task"),
        ("create", "task"),
        ("update", "task"),
    }
}


def require_permission(action: str, resource: str):
    """
    Global RBAC permission check. Verifies if the current user's role
    has the requested permission globally.
    """
    def permission_dependency(current_user=Depends(get_current_user)):
        if current_user.role and current_user.role.name == "admin":
            return current_user
        
        permissions = current_user.role.permissions if current_user.role else []
        allowed = any(
            perm.action == action and perm.resource == resource
            for perm in permissions
        )
        if not allowed:
            raise PermissionDeniedException(f"Global permission denied: requires {action} on {resource}")
        return current_user
    return permission_dependency


def _verify_project_access(
    db: Session, 
    project_id: uuid.UUID, 
    current_user: UserModel, 
    actor: str,
    action: str, 
    resource: str
) -> tuple[ProjectMember, UserModel] | None:
    """
    Core authorization logic for evaluating project-bound resources.
    Returns the ProjectMember if authorized, None if bypassed by an admin override,
    and raises PermissionDeniedException if unauthorized.
    """
    # Global admins bypass project-level checks
    # if current_user.role and current_user.role.name == "admin":
    #     return None
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    
    if not membership:
        raise PermissionDeniedException(f"You are not a member of project {project_id}.")
    
    if membership.role != actor:
        raise PermissionDeniedException(
            f"Project role '{membership.role}' does not match required actor '{actor}'."
        )
    
    allowed_permissions = PROJECT_ROLE_PERMISSIONS.get(membership.role, set())
    if (action, resource) not in allowed_permissions:
        raise PermissionDeniedException(
            f"Project role '{membership.role}' does not grant {action} on {resource}."
        )
    
    return (membership, current_user)


def require_project_permission(actor: str, action: str, resource: str):
    """
    Project-level permission check.
    """
    def permission_dependency(
            project_id: uuid.UUID,
            current_user=Depends(get_current_user),
            db=Depends(get_db)
    ):
        return _verify_project_access(db, project_id, current_user, actor, action, resource)
    return permission_dependency


def require_task_permission(actor: str, action: str, resource: str):
    """
    Task-level permission check. Resolves the task to its parent project
    and delegates to the core project access check.
    """
    def permission_dependency(
            task_id: uuid.UUID,
            current_user=Depends(get_current_user),
            db=Depends(get_db)
    ):
        # We need the task to determine which project to check
        task = db.get(Task, task_id)
        if not task:
            raise TaskNotFoundException(f"Task with ID '{task_id}' not found.")
        
        project_id = cast(uuid.UUID, task.project_id)
        return _verify_project_access(db, project_id, current_user, actor, action, resource)
        
    return permission_dependency
