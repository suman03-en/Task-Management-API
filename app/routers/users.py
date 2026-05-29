from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user import create_user, get_user, list_users

user_router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]


@user_router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user_in: UserCreate, db: DbSession):
    return create_user(db, user_in)


@user_router.get("", response_model=list[UserRead])
def list_users_endpoint(db: DbSession):
    return list_users(db)


@user_router.get("/{user_id}", response_model=UserRead)
def get_user_endpoint(user_id: str, db: DbSession):
    return get_user(db, user_id)
