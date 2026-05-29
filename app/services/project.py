from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project as ProjectModel
from app.models.user import User as UserModel
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project_in_db(db: Session, project_in: ProjectCreate) -> ProjectModel:
    if (
        project_in.owner_id is not None
        and db.get(ProjectModel, project_in.owner_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found.",
        )

    project_db = ProjectModel(**project_in.model_dump())
    db.add(project_db)
    db.commit()
    db.refresh(project_db)
    return project_db


def list_projects_from_db(db: Session):
    statement = select(ProjectModel).order_by(ProjectModel.created_at.desc())
    return db.scalars(statement).all()
    


def get_project_from_db(db: Session, project_id: str) -> ProjectModel:
    project = db.get(ProjectModel, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def update_project_in_db(
    db: Session, project_id: str, project_in: ProjectUpdate
) -> ProjectModel:
    project_db = db.get(ProjectModel, project_id)

    if not project_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project_db, field, value)

    db.commit()
    db.refresh(project_db)
    return project_db


def delete_project_from_db(db: Session, project_id: str) -> None:
    project = get_project_from_db(db, project_id)
    db.delete(project)
    db.commit()
