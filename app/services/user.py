import uuid
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User as UserModel
from app.schemas.user import UserCreate, TokenData, UserInDB
from app.dependencies import oauth_scheme
from app.auth.jwt_handler import decode_jwt_token
from app.auth.security import verify_password, get_password_hash
from app.dependencies import get_db
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException

def create_user_in_db(db: Session, user_in: UserCreate) -> UserModel:
    if get_user_by_username(db, user_in.username):
        raise UserAlreadyExistsException(f"User with username '{user_in.username}' already exists.")
    hashed_password = get_password_hash(user_in.password)
    user_db = UserModel(
        username=user_in.username,
        hashed_password=hashed_password
    )
    db.add(user_db)
    db.commit()
    db.refresh(user_db)

    return user_db


def list_users_from_db(db: Session) -> list[UserModel]:
    statement = select(UserModel).order_by(UserModel.created_at.desc())
    return list(db.scalars(statement).all())


def get_user_from_db(db: Session, user_id: uuid.UUID) -> UserModel:
    user_db = db.get(UserModel, user_id)
    if user_db is None:
        raise UserNotFoundException(f"User with ID '{user_id}' not found.")
    return user_db

def get_user_by_username(db: Session, username: str) -> UserModel | None:
    return db.query(UserModel).filter(UserModel.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username=username)
    if user and verify_password(password, user.hashed_password):
        return user 
    return None

def get_current_user(token: Annotated[str, Depends(oauth_scheme)], db: Session = Depends(get_db)) -> UserModel:
    payload = decode_jwt_token(token)
    username = payload.get("sub")
    if username is None:
        raise UserNotFoundException("Could not validate credentials.")
    token_data = TokenData(username=username)
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise UserNotFoundException("Could not validate credentials.")
    return user


    

