from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project as ProjectModel
from app.repositories.project import (
    create_project as create_project_repo,
    delete_project as delete_project_repo,
    get_project_by_id,
    list_projects as list_projects_repo,
    update_project as update_project_repo,
)
from app.repositories.user import get_user_by_id
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_in: ProjectCreate) -> ProjectModel:
    if (
        project_in.owner_id is not None
        and get_user_by_id(db, project_in.owner_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found.",
        )

    return create_project_repo(db, project_in)


def list_projects(db: Session):
    return list_projects_repo(db)


def get_project(db: Session, project_id: str) -> ProjectModel:
    project = get_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def update_project(
    db: Session, project_id: str, project_in: ProjectUpdate
) -> ProjectModel:
    project = get_project(db, project_id)

    if (
        project_in.owner_id is not None
        and get_user_by_id(db, project_in.owner_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found.",
        )

    return update_project_repo(db, project, project_in)


def delete_project(db: Session, project_id: str) -> None:
    project = get_project(db, project_id)
    delete_project_repo(db, project)
