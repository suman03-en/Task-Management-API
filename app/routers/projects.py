import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.task import TaskRead
from app.schemas.user import UserRead
from app.services.project import (
    add_project_member_in_db,
    create_project_in_db,
    delete_project_from_db,
    get_project_from_db,
    list_projects_from_db,
    list_project_members_from_db,
    remove_project_member_in_db,
    update_project_in_db,
)
from app.services.task import list_tasks_from_db

project_router = APIRouter(prefix="/projects", tags=["projects"])


DbSession = Annotated[Session, Depends(get_db)]


@project_router.post(
    "", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
def create_project(project_in: ProjectCreate, db: DbSession):
    project = create_project_in_db(db, project_in)
    return ProjectRead.model_validate(project)


@project_router.get("", response_model=list[ProjectRead])
def list_projects(db: DbSession):
    projects = list_projects_from_db(db)
    return [ProjectRead.model_validate(project) for project in projects]


@project_router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: DbSession):
    project = get_project_from_db(db, project_id)
    return ProjectRead.model_validate(project)


@project_router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: uuid.UUID, project_in: ProjectUpdate, db: DbSession):
    project = update_project_in_db(db, project_id, project_in)
    return ProjectRead.model_validate(project)


@project_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: uuid.UUID, db: DbSession):
    delete_project_from_db(db, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@project_router.get("/{project_id}/tasks", response_model=list[TaskRead])
def list_tasks(project_id: uuid.UUID, db: DbSession):
    tasks = list_tasks_from_db(project_id, db)
    return [TaskRead.model_validate(task) for task in tasks]


@project_router.get("/{project_id}/members", response_model=list[UserRead])
def list_project_members(project_id: uuid.UUID, db: DbSession):
    members = list_project_members_from_db(db, project_id)
    return [UserRead.model_validate(member) for member in members]


@project_router.post(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def add_project_member(project_id: uuid.UUID, user_id: uuid.UUID, db: DbSession):
    add_project_member_in_db(db, project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@project_router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_project_member(project_id: uuid.UUID, user_id: uuid.UUID, db: DbSession):
    remove_project_member_in_db(db, project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
