from typing import Annotated
from fastapi import APIRouter, Depends, status
import uuid
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.task import TaskCreate, TaskRead
from app.services.task import create_task_in_db, list_tasks_from_db


task_router = APIRouter(prefix="/tasks", tags=["tasks"])


DbSession = Annotated[Session, Depends(get_db)]


@task_router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: DbSession) -> TaskRead:
    return create_task_in_db(db, task_in)


    
