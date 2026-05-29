from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User as UserModel
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> UserModel:
    user = UserModel(**user_in.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: str) -> UserModel | None:
    return db.get(UserModel, user_id)


def get_user_by_username(db: Session, username: str) -> UserModel | None:
    statement = select(UserModel).where(UserModel.username == username)
    return db.scalar(statement)


def list_users(db: Session) -> Sequence[UserModel]:
    statement = select(UserModel).order_by(UserModel.created_at.desc())
    return db.scalars(statement).all()
