import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserRead


def create_user_in_db(db: Session, user_in: UserCreate) -> UserModel:
    user_db = UserModel(**user_in.model_dump())
    try:
        db.add(user_db)
        db.commit()
        db.refresh(user_db)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": f"Failed to create user in the database.",
                "error": str(e)
            }
        )
    return user_db


def list_users_from_db(db: Session) -> list[UserRead]:
    statement = select(UserModel).order_by(UserModel.created_at.desc())
    users_db = db.scalars(statement).all()
    users = [UserRead.model_validate(user_db) for user_db in users_db]
    return users


def get_user_from_db(db: Session, user_id: uuid.UUID) -> UserRead:
    user_db = db.get(UserModel, user_id)
    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    user = UserRead.model_validate(user_db)
    return user
