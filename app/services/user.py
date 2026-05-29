from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User as UserModel
from app.repositories.user import (
    create_user as create_user_repo,
    get_user_by_id,
    get_user_by_username,
    list_users as list_users_repo,
)
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> UserModel:
    if get_user_by_username(db, user_in.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )

    return create_user_repo(db, user_in)


def list_users(db: Session):
    return list_users_repo(db)


def get_user(db: Session, user_id: str) -> UserModel:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user
