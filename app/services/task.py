import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.project import Project
from app.schemas.task import TaskInDB, TaskUpdate
from app.core.exceptions import TaskNotFoundException, ProjectNotFoundException


def create_task_in_db(db: Session, task_in: TaskInDB) -> Task:
    if db.get(Project, task_in.project_id) is None:
        raise ProjectNotFoundException(f"Project with ID '{task_in.project_id}' not found.")
    task_db = Task(**task_in.model_dump())
    db.add(task_db)
    db.commit()
    db.refresh(task_db)
    return task_db


def list_tasks_from_db(project_id: uuid.UUID, db: Session) -> list[Task]:
    if db.get(Project, project_id) is None:
        raise ProjectNotFoundException(f"Project with ID '{project_id}' not found.")
    tasks_db = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
        .all()
    )
    return tasks_db

def get_task_count_from_db(project_id: uuid.UUID, db: Session) -> int:
    if db.get(Project, project_id) is None:
        raise ProjectNotFoundException(f"Project with ID '{project_id}' not found.")
    count = db.query(Task).filter(Task.project_id == project_id).count()
    return count

def get_task_from_db(task_id: uuid.UUID, db: Session) -> Task:
    task_db = db.get(Task, task_id)
    if task_db is None:
        raise TaskNotFoundException(f"Task with ID '{task_id}' not found.")
    return task_db


def update_task_in_db(task_id: uuid.UUID, task_update: TaskUpdate, db: Session) -> Task:
    task_db = db.get(Task, task_id)
    if task_db is None:
        raise TaskNotFoundException(f"Task with ID '{task_id}' not found.")
    for field, value in task_update.model_dump(exclude_unset=True).items():
        setattr(task_db, field, value)
    db.commit()
    db.refresh(task_db)
    return task_db


def delete_task_from_db(task_id: uuid.UUID, db: Session) -> None:
    task_db = db.get(Task, task_id)
    if task_db is None:
        raise TaskNotFoundException(f"Task with ID '{task_id}' not found.")
    db.delete(task_db)
    db.commit()
