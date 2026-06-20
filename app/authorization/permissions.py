from fastapi import Depends, HTTPException, status
from app.services.user import get_current_user

def require_permission(action: str, resource: str):
    def permission_dependency(current_user=Depends(get_current_user)):
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
