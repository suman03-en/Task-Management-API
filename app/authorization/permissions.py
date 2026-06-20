import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from app.services.user import get_current_user
from app.dependencies import get_db
from app.models.project import ProjectMember


PROJECT_ROLE_PERMISSIONS = {
    "creator": {
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
    def permission_dependency(current_user=Depends(get_current_user)):
        if current_user.role.name == "admin":
            return current_user
        permissions = current_user.role.permissions
        allowed = any(
            perm.action == action and perm.resource == resource
            for perm in permissions
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return current_user
    return permission_dependency


def require_project_permission(action: str, resource: str):
    """
    Dependency to check if the current user has permission to perform an action on a project resource.

    Args:
        action (str): The action being performed (e.g., "create", "read", "update", "delete").
        resource (str): resource type (e.g., "project", "task").
    """
    def permission_dependency(
            project_id: uuid.UUID,
            current_user=Depends(get_current_user),
            db=Depends(get_db)
            ):
        #fetch membership of the user in the project
        membership = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id
            )
        )
        if not membership:
            raise HTTPException(403)
        
        role = membership.role

        allowed_permissions = PROJECT_ROLE_PERMISSIONS.get(role, set())
        if (action, resource) not in allowed_permissions:
            raise HTTPException(403)
        
        return membership
    return permission_dependency
        
        

