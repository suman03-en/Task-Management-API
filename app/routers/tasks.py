import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas.task import TaskRead, TaskUpdate
from app.services.task import (
    get_task_from_db,
    update_task_in_db,
    delete_task_from_db,
    assign_task_to_user_in_db,
    complete_task_in_db,
)
from app.models.user import User as UserModel
from app.models.project import ProjectMember
from app.authorization.permissions import require_task_permission


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]

task_router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])


@task_router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: uuid.UUID, db: DbSession, _: ProjectMember = Depends(require_task_permission("read", "task"))):
    return get_task_from_db(db, task_id)


@task_router.patch(
    "/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK
)
def update_task(
    task_id: uuid.UUID, 
    task_update: TaskUpdate,
    db: DbSession,
    _: ProjectMember = Depends(require_task_permission("update", "task"))
):
    return update_task_in_db(db, task_id, task_update)


@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: uuid.UUID, db: DbSession, _: ProjectMember = Depends(require_task_permission("delete", "task"))):
    return delete_task_from_db(db, task_id)


@task_router.post("/{task_id}/complete", response_model=TaskRead)
def mark_task_complete(task_id: uuid.UUID, db: DbSession, _: ProjectMember = Depends(require_task_permission("update", "task"))):
    return complete_task_in_db(db, task_id)


@task_router.post("/{task_id}/assign", response_model=TaskRead)
def assign_task_to_user(task_id: uuid.UUID, user_id: Annotated[uuid.UUID, Body(embed=True)], db: DbSession, _: ProjectMember = Depends(require_task_permission("update", "task"))):
    return assign_task_to_user_in_db(db, task_id, user_id)
