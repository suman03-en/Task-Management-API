from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserRead, Token, RefreshTokenRequest
from app.models.user import User as UserModel
from app.services.user import UserService
from app.auth.jwt_handler import create_access_token
from app.authorization.permissions import require_permission
from app.schemas.pagination import PaginatedResponse
from app.dependencies.users import get_current_user
from app.dependencies.db import get_db
from app.dependencies.services import get_user_service

# Main router for all user-related endpoints
user_router = APIRouter(prefix="/users", tags=["users"])


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
CurrentUser = Annotated[UserModel, Depends(get_current_user)]


# --- Public / Auth Endpoints ---

@user_router.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, user_service: UserServiceDep):
    return user_service.create_user(user_in)


@user_router.post("/auth/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        user_service: UserServiceDep
):
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = user_service.create_refresh_token(user)

    return Token(
        access_token=access_token, 
        refresh_token=refresh_token,
        token_type="bearer"
    )


@user_router.post("/auth/refresh", response_model=Token)
async def refresh_access_token(
    request: RefreshTokenRequest,
    user_service: UserServiceDep
):
    user = user_service.verify_refresh_token(request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = user_service.create_refresh_token(user) # rotate token
    
    return Token(
        access_token=access_token, 
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


# --- Protected Endpoints ---

@user_router.get("", response_model=PaginatedResponse[UserRead])
def list_users(
    user_service: UserServiceDep,
    _: UserModel = Depends(require_permission("read", "user")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    users, total = user_service.list_users(offset=offset, limit=page_size)
    return PaginatedResponse(items=users, total=total, page=page, page_size=page_size)


@user_router.get("/me", response_model=UserRead)
async def read_users_me(
        current_user: CurrentUser
):
    # current_user relies on Depends(get_current_user), so it's fully protected
    return current_user


@user_router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, user_service: UserServiceDep, _: UserModel = Depends(require_permission("read", "user"))):
    return user_service.get_user(user_id)
