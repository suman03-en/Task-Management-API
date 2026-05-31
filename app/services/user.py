import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User as UserModel
from app.schemas.user import UserCreate


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
                "error": str(e),
            },
        )
    return user_db


def list_users_from_db(db: Session) -> list[UserModel]:
    statement = select(UserModel).order_by(UserModel.created_at.desc())
    return list(db.scalars(statement).all())


def get_user_from_db(db: Session, user_id: uuid.UUID) -> UserModel:
    user_db = db.get(UserModel, user_id)
    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user_db
