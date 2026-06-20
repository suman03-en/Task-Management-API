from app.services.user import create_user_in_db
from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.models.authorization import Role

def input_admin_credentials():
    print("Enter admin credentials:")
    username = input("Username: ")
    password = input("Password: ")
    return username, password

def create_admin_user(username: str, password: str):
    db = SessionLocal()
    try:
        # Check if admin role exists, if not create it
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        # Create admin user
        admin_user_data = UserCreate(
            username=username,
            password=password,
            role_id=admin_role.id # type: ignore
        )
        print("Creating admin user...")
        create_user_in_db(db, admin_user_data)
    finally:
        db.close()

if __name__ == "__main__":
    username, password = input_admin_credentials()
    create_admin_user(username, password)
    print("Admin user created successfully.")