from typing import Annotated
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.user import UserCreate, UserRead, Token
from app.models.user import User as UserModel
from app.services.user import create_user_in_db, get_user_from_db, list_users_from_db, authenticate_user, get_current_user
from app.auth.jwt_handler import create_access_token



user_router = APIRouter(prefix="/users", tags=["users"])

#subrouter
public_router = APIRouter(prefix="/auth")
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

# Annotated types for dependencies
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[UserModel, Depends(get_current_user)]

@public_router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: DbSession):
    return create_user_in_db(db, user_in)


@protected_router.get("/list", response_model=list[UserRead])
def list_users(db: DbSession):
    return list_users_from_db(db)

@protected_router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: DbSession):
    return get_user_from_db(db, user_id)


@public_router.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: DbSession
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return Token(access_token=access_token, token_type="bearer")

@protected_router.get("/users/me", response_model=UserRead)
async def read_users_me(
        current_user: CurrentUser
):
    return current_user


# Include subrouters in the main router
user_router.include_router(public_router)
user_router.include_router(protected_router)
