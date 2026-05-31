from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user import create_user_in_db, get_user_from_db, list_users_from_db

user_router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]


@user_router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: DbSession):
    return create_user_in_db(db, user_in)

@user_router.get("", response_model=list[UserRead])
def list_users(db: DbSession):
    return list_users_from_db(db)

@user_router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: DbSession):
    return get_user_from_db(db, user_id)
