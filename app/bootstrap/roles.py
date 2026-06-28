from app.db.database import SessionLocal
from app.models.authorization import Role

ROLE_CACHE = {}

def load_roles():
    """
    Load roles from the database into the ROLE_CACHE dictionary.
    This caches the roles for quick access and ensures that required roles are present in the database.
    """
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        for role in roles:
            ROLE_CACHE[role.name] = role.id
        required_roles = {"user", "admin"}
        missing_roles = required_roles - ROLE_CACHE.keys()
        if missing_roles:
            raise RuntimeError(f"Missing roles in database: {missing_roles}")
    finally:
        db.close()
