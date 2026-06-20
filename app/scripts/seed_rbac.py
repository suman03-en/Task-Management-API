from sqlalchemy import select 
from app.models.authorization import Role, Permission, RolePermission
from app.db.database import SessionLocal

mapping = {
    "admin": "all",
    "user": [
        ("create", "project"),
        ("read", "project"),
        ("update", "project"),
        ("delete", "project"),
        ("create", "task"),
        ("read", "task"),
        ("update", "task"),
        ("delete", "task"),
        # ("add_member", "project_members"),
        # ("remove_member", "project_members")
    ]
}

def create_roles():
    roles = [
        Role(name="admin"),
        Role(name="user")  # Role for regular users
    ]
    return roles

def create_permissions():
    permissions = [
        Permission(action="create", resource="project"),
        Permission(action="read", resource="project"),
        Permission(action="update", resource="project"),
        Permission(action="delete", resource="project"),
        Permission(action="create", resource="task"),
        Permission(action="read", resource="task"),
        Permission(action="update", resource="task"),
        Permission(action="delete", resource="task"),
        Permission(action="add_member", resource="project_members"),
        Permission(action="remove_member", resource="project_members"),
        Permission(action="add_role", resource="roles"),
        Permission(action="remove_role", resource="roles"),
        Permission(action="add_permission", resource="permissions"),
        Permission(action="remove_permission", resource="permissions"),
        Permission(action="delete_users", resource="users"),

    ]
    return permissions

def check_roles_exists(db, role_name):
    return db.scalar(select(Role).where(Role.name == role_name)) is not None

def check_permissions_exists(db, action, resource):
    return db.scalar(select(Permission).where(
        Permission.action == action,
        Permission.resource == resource
    )) is not None

def check_role_permission_exists(db, role_id, permission_id):
    return db.scalar(select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    )) is not None

def seed_rbac():
    """
    Seed initial RBAC data: roles, permissions, and role-permission mappings.
    """

    db = SessionLocal()
    roles = create_roles()
    permissions = create_permissions()

    # add roles and permissions to the db
    try:
        for role in roles:
            exists = check_roles_exists(db, role.name)
            if not exists:
                print(f"Adding role: {role.name}")
                db.add(role)
        
        for permission in permissions:
            exists = check_permissions_exists(db, permission.action, permission.resource)
            if not exists:
                print(f"Adding permission: {permission.action} {permission.resource}")
                db.add(permission)
        db.flush()  # flush to get IDs for role-permission mapping
        
        # assign permissions to roles based on the mapping
        for role_name, perms in mapping.items():
            role = db.scalar(select(Role).where(Role.name == role_name))
            if role:
                if perms == "all":
                    continue  # admin will have all permissions by default
                for perm in perms:
                    action, resource = perm
                    permission = db.scalar(select(Permission).where(
                        Permission.action == action,
                        Permission.resource == resource
                    ))
                    if permission:
                        exists = check_role_permission_exists(db, role.id, permission.id)
                        if not exists:
                            role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
                            print(f"Assigning permission: {permission.action} {permission.resource} to role: {role.name}")
                            db.add(role_permission)
        db.commit()
        print("RBAC data seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding RBAC data: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding RBAC data...")
    seed_rbac()
