import uuid
import secrets

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.user import User as UserModel
from app.models.authorization import Role
from app.schemas.user import UserCreate
from app.auth.security import verify_password, get_password_hash
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException
from app.bootstrap.roles import ROLE_CACHE

def get_user_by_username(db: Session, username: str) -> UserModel | None:
    return db.scalar(select(UserModel).where(UserModel.username == username))


def authenticate_user(db: Session, username: str, password: str) -> UserModel | None:
    user = get_user_by_username(db, username=username)
    if user and verify_password(password, user.hashed_password):
        return user 
    return None

def create_refresh_token_for_user(db: Session, user: UserModel) -> str:
    """Generates a secure opaque token embedded with the username, hashes the secret part, and stores it in the DB."""
    secret = secrets.token_urlsafe(32)
    hashed_secret = get_password_hash(secret)
    user.hashed_refresh_token = hashed_secret
    db.commit()
    return f"{user.username}::{secret}"

def verify_refresh_token(db: Session, raw_token: str) -> UserModel | None:
    """Parses a refresh token, looks up the user, and verifies the hash."""
    try:
        username, secret = raw_token.split("::", 1)
    except ValueError:
        return None
        
    user = get_user_by_username(db, username=username)
    if not user or not user.hashed_refresh_token:
        return None
        
    if verify_password(secret, user.hashed_refresh_token):
        return user
    return None

def create_user_in_db(db: Session, user_in: UserCreate, role_id: uuid.UUID | None = None) -> UserModel:
    if role_id is None:
        role_id = ROLE_CACHE["user"]

    hashed_password = get_password_hash(user_in.password)
    user_db = UserModel(
        username=user_in.username,
        hashed_password=hashed_password,
        role_id=role_id
    )
    db.add(user_db)
    try:
        db.commit()
        db.refresh(user_db)
    except Exception:
        db.rollback()
        raise UserAlreadyExistsException(f"User with username '{user_in.username}' already exists.")

    return user_db


def list_users_from_db(db: Session, offset: int, limit: int) -> tuple[list[UserModel], int]:
    base_query = select(UserModel)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    users_db = list(
        db.scalars(
            base_query.order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
        ).all()
    )
    return users_db, total


def get_user_from_db(db: Session, user_id: uuid.UUID) -> UserModel:
    user_db = db.get(UserModel, user_id)
    if user_db is None:
        raise UserNotFoundException(f"User with ID '{user_id}' not found.")
    return user_db


