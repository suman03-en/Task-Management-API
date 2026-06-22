import logging
import uuid
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import SessionLocal
from app.auth.jwt_handler import decode_jwt_token
from app.models.user import User as UserModel
from app.models.authorization import Role, Permission


logger = logging.getLogger(__name__)

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/auth/token")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Annotated[str, Depends(oauth_scheme)],
    db: Session = Depends(get_db),
) -> UserModel:
    """
    FastAPI dependency that decodes the Bearer token and returns the
    authenticated User, with role and permissions eagerly loaded to
    avoid N+1 queries in downstream permission checks.
    """
    payload = decode_jwt_token(token)
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = (
        select(UserModel)
        .where(UserModel.username == username)
        .options(
            selectinload(UserModel.role).selectinload(Role.permissions)
        )
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or has been deleted.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
