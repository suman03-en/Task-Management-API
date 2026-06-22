import uuid
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import DateTime, String, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import utc_now
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.authorization import Role
    from app.models.project import Project
    from app.models.task import Task

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        nullable=False
    )
    hashed_refresh_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user")
    assigned_tasks = relationship("Task", back_populates="assigned_user")