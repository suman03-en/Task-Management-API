import uuid
from fastapi import HTTPException, status
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.models.task import Task
from app.models.project import Project
from sqlalchemy.orm import Session


def create_task_in_db(db: Session, task_in: TaskCreate) -> TaskRead:
    task_db = Task(**task_in.model_dump())
    db.add(task_db)
    db.commit()
    db.refresh(task_db)
    return TaskRead.model_validate(task_db)

def list_tasks_from_db(project_id: uuid.UUID, db: Session) -> list[TaskRead]:
    if db.get(Project, project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    tasks_db = db.query(Task).filter(Task.project_id == project_id).order_by(Task.created_at.desc()).all()
    return [TaskRead.model_validate(task_db) for task_db in tasks_db]


def get_task_from_db(task_id: uuid.UUID, db: Session) -> TaskRead:
    task_db = db.get(Task, task_id)
    if task_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return TaskRead.model_validate(task_db)

def update_task_in_db(task_id: uuid.UUID, task_update: TaskUpdate, db: Session) -> TaskRead:
    task_db = db.get(Task, task_id)
    if task_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    for field, value in task_update.model_dump(exclude_unset=True).items():
        setattr(task_db, field, value)
    db.commit()
    db.refresh(task_db)
    return TaskRead.model_validate(task_db)
    

def delete_task_from_db(task_id: uuid.UUID, db: Session) -> None:
    task_db = db.get(Task, task_id)
    if task_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    db.delete(task_db)
    db.commit()
