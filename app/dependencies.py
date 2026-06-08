from fastapi.security import OAuth2PasswordBearer
from app.db.database import SessionLocal


oauth_scheme = OAuth2PasswordBearer(tokenUrl="users/auth/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
