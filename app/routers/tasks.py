import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.dependencies.users import get_current_user
from app.dependencies.services import get_task_service
from app.schemas.task import TaskRead, TaskUpdate
from app.services.task import TaskService
from app.models.user import User as UserModel
from app.models.project import ProjectMember
from app.authorization.permissions import require_task_permission


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]

task_router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])


@task_router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: uuid.UUID, task_service: TaskServiceDep, _: ProjectMember = Depends(require_task_permission("read", "task"))):
    return task_service.get_task(task_id)


@task_router.patch(
    "/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK
)
def update_task(
    task_id: uuid.UUID, 
    task_update: TaskUpdate,
    task_service: TaskServiceDep,
    _: ProjectMember = Depends(require_task_permission("update", "task"))
):
    return task_service.update_task(task_id, task_update)


@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: uuid.UUID, task_service: TaskServiceDep, _: ProjectMember = Depends(require_task_permission("delete", "task"))):
    return task_service.delete_task(task_id)


@task_router.post("/{task_id}/complete", response_model=TaskRead)
def mark_task_complete(task_id: uuid.UUID, task_service: TaskServiceDep, _: ProjectMember = Depends(require_task_permission("update", "task"))):
    return task_service.complete_task(task_id)


@task_router.post("/{task_id}/assign", response_model=TaskRead)
def assign_task_to_user(task_id: uuid.UUID, user_id: Annotated[uuid.UUID, Body(embed=True)], task_service: TaskServiceDep, _: ProjectMember = Depends(require_task_permission("update", "task"))):
    return task_service.assign_task_to_user(task_id, user_id)
