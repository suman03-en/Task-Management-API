from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project as ProjectModel
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_in: ProjectCreate) -> ProjectModel:
    project = ProjectModel(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project_by_id(db: Session, project_id: str) -> ProjectModel | None:
    return db.get(ProjectModel, project_id)


def list_projects(db: Session) -> Sequence[ProjectModel]:
    statement = select(ProjectModel).order_by(ProjectModel.created_at.desc())
    return db.scalars(statement).all()


def update_project(
    db: Session,
    project: ProjectModel,
    project_in: ProjectUpdate,
) -> ProjectModel:
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: ProjectModel) -> None:
    db.delete(project)
    db.commit()
