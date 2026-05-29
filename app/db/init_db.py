from sqlalchemy import inspect, text

from .base import Base
from .session import engine


def _migrate_sqlite_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "projects" not in table_names:
        return

    project_columns = {column["name"] for column in inspector.get_columns("projects")}

    alter_statements = []
    if "owner_id" not in project_columns:
        alter_statements.append("ALTER TABLE projects ADD COLUMN owner_id VARCHAR(36)")
    if "created_at" not in project_columns:
        alter_statements.append("ALTER TABLE projects ADD COLUMN created_at DATETIME")
    if "updated_at" not in project_columns:
        alter_statements.append("ALTER TABLE projects ADD COLUMN updated_at DATETIME")

    if not alter_statements:
        return

    with engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))

        connection.execute(text("""
                UPDATE projects
                SET
                    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                """))


def init_db():
    Base.metadata.create_all(bind=engine)
    if engine.url.get_backend_name() == "sqlite":
        _migrate_sqlite_schema()
