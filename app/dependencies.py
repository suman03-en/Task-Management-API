import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.project import Project


oauth_scheme = OAuth2PasswordBearer(tokenUrl="users/auth/token")

    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



