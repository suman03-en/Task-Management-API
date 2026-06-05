import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.project import (
    ProjectCreate, 
    ProjectRead, 
    ProjectUpdate, 
    ProjectMemberAdd, 
    ProjectMemberRead
)
from app.schemas.task import TaskRead, TaskListResponse, TaskCreate, TaskInDB
from app.schemas.user import UserRead, ProjectMember
from app.services.project import (
    add_project_member_in_db,
    create_project_in_db,
    delete_project_from_db,
    get_project_from_db,
    list_projects_from_db,
    list_project_members_from_db,
    remove_project_member_from_db,
    update_project_in_db,
)
from app.services.task import list_tasks_from_db, get_task_count_from_db, create_task_in_db

project_router = APIRouter(prefix="/projects", tags=["projects"])

DbSession = Annotated[Session, Depends(get_db)]


@project_router.post(
    "", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
def create_project(project_in: ProjectCreate, db: DbSession):
    return create_project_in_db(db, project_in)


@project_router.get("", response_model=list[ProjectRead])
def list_projects(db: DbSession):
    return list_projects_from_db(db)


@project_router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: DbSession):
    return get_project_from_db(db, project_id)


@project_router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: uuid.UUID, project_in: ProjectUpdate, db: DbSession):
    return update_project_in_db(db, project_id, project_in)


@project_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: uuid.UUID, db: DbSession):
    delete_project_from_db(db, project_id)

@project_router.post("/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task_for_project(project_id: uuid.UUID, task_in: TaskCreate, db: DbSession):
    task_in_db = TaskInDB(**task_in.model_dump(), project_id=project_id)
    return create_task_in_db(db, task_in_db)

@project_router.get("/{project_id}/tasks", response_model=TaskListResponse)
def list_tasks(project_id: uuid.UUID, db: DbSession):
    db_tasks = list_tasks_from_db(project_id, db)
    tasks = [TaskRead.model_validate(task) for task in db_tasks]
    count = get_task_count_from_db(project_id, db)
    return TaskListResponse(tasks=tasks, count=count)


@project_router.get("/{project_id}/members", response_model=list[UserRead])
def list_project_members(project_id: uuid.UUID, db: DbSession):
    return list_project_members_from_db(db, project_id)


@project_router.post(
    "/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED
)
def add_project_member(project_id: uuid.UUID, member_in: ProjectMemberAdd, db: DbSession):
   return add_project_member_in_db(db, project_id, member_in)



@project_router.delete(
    "/{project_id}/members", status_code=status.HTTP_204_NO_CONTENT
)
def remove_project_member(project_id: uuid.UUID, member_in: ProjectMemberAdd, db: DbSession):
    remove_project_member_from_db(db, project_id, member_in)
