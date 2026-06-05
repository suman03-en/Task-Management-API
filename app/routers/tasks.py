from typing import Annotated
from fastapi import APIRouter, Depends, status
import uuid
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task import (
    get_task_from_db,
    update_task_in_db,
    delete_task_from_db,
)

task_router = APIRouter(prefix="/tasks", tags=["tasks"])

DbSession = Annotated[Session, Depends(get_db)]


@task_router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: uuid.UUID, db: DbSession):
    return get_task_from_db(task_id, db)


@task_router.patch(
    "/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK
)
def update_task(task_id: uuid.UUID, task_update: TaskUpdate, db: DbSession):
    return update_task_in_db(task_id, task_update, db)


@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: uuid.UUID, db: DbSession):
    return delete_task_from_db(task_id, db)
