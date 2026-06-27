import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.dependencies.users import get_current_user
from app.dependencies.services import get_project_service, get_task_service
from app.models.user import User as UserModel
from app.models.project import ProjectMember
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectMemberAdd,
    ProjectMemberRead,
)
from app.schemas.task import TaskRead, TaskCreate, TaskCreateData
from app.schemas.user import UserRead
from app.schemas.pagination import PaginatedResponse
from app.services.project import ProjectService
from app.services.task import TaskService
from app.authorization.permissions import require_project_permission

CurrentUser = Annotated[UserModel, Depends(get_current_user)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


project_router = APIRouter(
    prefix="/projects", tags=["projects"], dependencies=[Depends(get_current_user)]
)


@project_router.post(
    "", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
def create_project(project_in: ProjectBase, current_user: CurrentUser, project_service: ProjectServiceDep):
    project_create = ProjectCreate(**project_in.model_dump())
    return project_service.create_project(project_create, current_user)


@project_router.get("", response_model=PaginatedResponse[ProjectRead])
def list_projects(
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    projects, total = project_service.list_projects(offset=offset, limit=page_size, current_user=current_user)
    return PaginatedResponse(
        items=projects, total=total, page=page, page_size=page_size
    )


@project_router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("read", "project")),
):
    return project_service.get_project(project_id, current_user)

@project_router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("update", "project")),
):
    return project_service.update_project(project_id, project_in, current_user)


@project_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("delete", "project")),
):
    project_service.delete_project(project_id, current_user)


@project_router.post(
    "/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED
)
def create_task_for_project(
    project_id: uuid.UUID,
    task_in: TaskCreate,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("create", "task")),
):
    task_in_db = TaskCreateData(**task_in.model_dump(), project_id=project_id)
    return project_service.create_task(task_in_db, current_user)


@project_router.get("/{project_id}/tasks", response_model=PaginatedResponse[TaskRead])
def list_tasks(
    project_id: uuid.UUID,
    task_service: TaskServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("read", "task")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    tasks, total = task_service.list_tasks(project_id, offset=offset, limit=page_size)
    return PaginatedResponse(items=tasks, total=total, page=page, page_size=page_size)


@project_router.get("/{project_id}/members", response_model=list[UserRead])
def list_project_members(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("read", "project")),
):
    return project_service.list_project_members(project_id, current_user)


@project_router.post(
    "/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_project_member(
    project_id: uuid.UUID,
    member_in: ProjectMemberAdd,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("add_member", "project")),
):
    return project_service.add_project_member(project_id, member_in, current_user)


@project_router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUser,
    _: ProjectMember = Depends(require_project_permission("remove_member", "project")),
):
    project_service.remove_project_member(project_id, user_id, current_user)
