import uuid
import logging
from typing import cast
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.project import Project
from app.schemas.task import TaskCreateData, TaskUpdate
from app.core.exceptions import (
    TaskNotFoundException,
    ProjectNotFoundException,
    PermissionDeniedException,
)
from app.services.project import check_project_membership

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_in: TaskCreateData) -> Task:
        project = self.db.get(Project, task_in.project_id)
        if project is None:
            raise ProjectNotFoundException(
                f"Project with ID '{task_in.project_id}' not found."
            )

        task_db = Task(**task_in.model_dump())
        self.db.add(task_db)
        self.db.commit()
        self.db.refresh(task_db)

        logger.debug("Task created: %s", task_db.id)
        return task_db
    
    def list_tasks(self, project_id: uuid.UUID, offset: int = 0, limit: int = 20) -> tuple[list[Task], int]:
        project = self.db.get(Project, project_id)
        if project is None:
            raise ProjectNotFoundException(f"Project with ID '{project_id}' not found.")

        base_query = select(Task).where(Task.project_id == project_id)
        total = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        tasks_db = list(
            self.db.scalars(
                base_query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
            ).all()
        )
        return tasks_db, total

    def get_task(self, task_id: uuid.UUID) -> Task:
        task_db = self.db.get(Task, task_id)
        if task_db is None:
            raise TaskNotFoundException(f"Task with ID '{task_id}' not found.")
        return task_db
    
    def update_task(self, task_id: uuid.UUID, task_update: TaskUpdate) -> Task:
        task_db = self.get_task(task_id)

        for field, value in task_update.model_dump(exclude_unset=True).items():
            setattr(task_db, field, value)

        self.db.commit()
        self.db.refresh(task_db)
        return task_db

    def delete_task(self, task_id: uuid.UUID) -> None:
        task_db = self.get_task(task_id)
        self.db.delete(task_db)
        self.db.commit()

    def complete_task(self, task_id: uuid.UUID) -> Task:
        task_db = self.get_task(task_id)
        task_db.status = "completed"
        self.db.commit()
        self.db.refresh(task_db)
        return task_db
    
    def assign_task_to_user(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task_db = self.get_task(task_id)

        project_id = cast(uuid.UUID, task_db.project_id)
        if not check_project_membership(self.db, project_id, user_id):
            raise PermissionDeniedException(
                f"User  is not a member of project."
            )

        task_db.assigned_to = user_id
        self.db.commit()
        self.db.refresh(task_db)
        return task_db
