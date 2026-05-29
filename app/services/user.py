from collections.abc import Sequence
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User as UserModel
from app.schemas.user import UserCreate


def create_user_in_db(db: Session, user_in: UserCreate) -> UserModel:
    if db.get(UserModel, user_in.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )

    user_db = UserModel(**user_in.model_dump())
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db


def list_users_in_db(db: Session) -> Sequence[UserModel]:
    statement = select(UserModel).order_by(UserModel.created_at.desc())
    return db.scalars(statement).all()


def get_user_from_db(db: Session, user_id: str) -> UserModel:
    user = db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user
