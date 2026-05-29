from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

project_router = APIRouter(prefix="/projects", tags=["projects"])


DbSession = Annotated[Session, Depends(get_db)]


@project_router.post(
    "", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
def create_project_endpoint(project_in: ProjectCreate, db: DbSession):
    return create_project(db, project_in)


@project_router.get("", response_model=list[ProjectRead])
def list_projects_endpoint(db: DbSession):
    return list_projects(db)


@project_router.get("/{project_id}", response_model=ProjectRead)
def get_project_endpoint(project_id: str, db: DbSession):
    return get_project(db, project_id)


@project_router.patch("/{project_id}", response_model=ProjectRead)
def update_project_endpoint(project_id: str, project_in: ProjectUpdate, db: DbSession):
    return update_project(db, project_id, project_in)


@project_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(project_id: str, db: DbSession):
    delete_project(db, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
