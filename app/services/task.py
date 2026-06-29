import uuid
import logging
from sqlalchemy import select, func, exists
from sqlalchemy.orm import Session

from app.models.task import Task, TaskRequestRecord
from app.models.project import Project
from app.schemas.task import TaskCreateData, TaskUpdate
from app.core.exceptions import (
    TaskNotFoundException,
    ProjectNotFoundException,
    TaskAlreadyAssignedException,
    InvalidTaskStateException,
    DuplicateTaskRequestException
)
from app.core.constants import TaskStatus


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
        if task_db.status == TaskStatus.IN_PROGRESS:
            task_db.status = TaskStatus.COMPLETED
        else:
            raise InvalidTaskStateException(
                f"Task is not in a state that allows completion."
            )
        self.db.commit()
        self.db.refresh(task_db)
        return task_db
       

    def assign_task_to_user(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task_db = self.get_task(task_id)
        if task_db.status != TaskStatus.PENDING:
            raise InvalidTaskStateException(
                f"Task is not in a state that allows assignment."
            )
        if task_db.assigned_to is not None:
            raise TaskAlreadyAssignedException(
                f"Task is already assigned to another user."
            )
        task_db.assigned_to = user_id
        task_db.status = TaskStatus.IN_PROGRESS
        self.db.commit()
        self.db.refresh(task_db)
        return task_db
    

class TaskRequestService:
    def __init__(self, db: Session, task_service: TaskService):
        self.db = db
        self.task_service = task_service

    def create_request(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskRequestRecord:
        """Create a task request record for a user requesting a task to get assigned to it."""
        task_db = self.task_service.get_task(task_id)
        if task_db.status != TaskStatus.PENDING:
            raise InvalidTaskStateException(
                f"Task is not in a state that allows requests."
            )
        existing_request = self.db.scalar(
            select(
                exists().where(
                    TaskRequestRecord.task_id == task_id,
                    TaskRequestRecord.request_by == user_id,
                )
            )
        )
        if existing_request:
            raise DuplicateTaskRequestException(
                f"User has already requested this task."
            )

        request_record = TaskRequestRecord(task_id=task_id, request_by=user_id)
        self.db.add(request_record)
        self.db.commit()
        self.db.refresh(request_record)
        return request_record
    
    def list_requests(self, task_id: uuid.UUID) -> list[TaskRequestRecord]:
        """List all task request records for a specific task."""
        task_db = self.task_service.get_task(task_id)
        return list(task_db.request_records)

    def list_user_requests(self, user_id: uuid.UUID) -> list[TaskRequestRecord]:
        """List all task request records made by a specific user."""
        return list(
                self.db.scalars(
                    select(TaskRequestRecord).where(TaskRequestRecord.request_by == user_id)
                ).all()
            )