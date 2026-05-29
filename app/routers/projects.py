from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project import (
    create_project_in_db,
    delete_project_from_db,
    get_project_from_db,
    list_projects_from_db,
    update_project_in_db,
)

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
def get_project(project_id: str, db: DbSession):
    return get_project_from_db(db, project_id)


@project_router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, project_in: ProjectUpdate, db: DbSession):
    return update_project_in_db(db, project_id, project_in)


@project_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: DbSession):
    delete_project_from_db(db, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
