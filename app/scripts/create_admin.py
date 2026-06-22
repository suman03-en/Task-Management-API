import getpass
from sqlalchemy import select

from app.services.user import create_user_in_db
from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.models.authorization import Role


def input_admin_credentials() -> tuple[str, str]:
    print("Enter admin credentials:")
    username = input("Username: ")
    password = getpass.getpass("Password: ")  # hidden input — no terminal echo
    return username, password


def create_admin_user(username: str, password: str) -> None:
    db = SessionLocal()
    try:
        admin_role = db.scalar(select(Role).where(Role.name == "admin"))
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        admin_user_data = UserCreate(username=username, password=password)
        print("Creating admin user...")
        create_user_in_db(db, admin_user_data, role_id=admin_role.id)  # type: ignore[arg-type]
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    username, password = input_admin_credentials()
    create_admin_user(username, password)