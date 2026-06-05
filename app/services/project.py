import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project as ProjectModel
from app.models.project import ProjectMember as ProjectMemberModel
from app.models.user import User as UserModel
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberAdd
from app.core.exceptions import ProjectNotFoundException, UserNotFoundException, MemberRemovalError


def create_project_in_db(db: Session, project_in: ProjectCreate) -> ProjectModel:
    if db.get(UserModel, project_in.owner_id) is None:
        raise UserNotFoundException(f"Owner with ID '{project_in.owner_id}' not found.")

    project_db = ProjectModel(**project_in.model_dump())
    db.add(project_db)
    db.commit()
    db.refresh(project_db)
    return project_db


def list_projects_from_db(db: Session):
    statement = select(ProjectModel).order_by(ProjectModel.created_at.desc())
    return db.scalars(statement).all()


def get_project_from_db(db: Session, project_id: uuid.UUID) -> ProjectModel:
    project = db.get(ProjectModel, project_id)
    if project is None:
        raise ProjectNotFoundException(f"Project with ID '{project_id}' not found.")
    return project


def update_project_in_db(
    db: Session, project_id: uuid.UUID, project_in: ProjectUpdate
) -> ProjectModel:
    project_db = db.get(ProjectModel, project_id)

    if not project_db:
        raise ProjectNotFoundException(f"Project with ID '{project_id}' not found.")

    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project_db, field, value)

    db.commit()
    db.refresh(project_db)
    return project_db


def delete_project_from_db(db: Session, project_id: uuid.UUID) -> None:
    project = get_project_from_db(db, project_id)
    db.delete(project)
    db.commit()


def add_project_member_in_db(
    db: Session, project_id: uuid.UUID, member_in: ProjectMemberAdd
) -> ProjectMemberModel:
    project = get_project_from_db(db, project_id)
    user = db.get(UserModel, member_in.user_id)

    if not user:
        raise UserNotFoundException(f"User with ID '{member_in.user_id}' not found.")

    existing_membership = db.get(ProjectMemberModel, (project.id, user.id))
    if existing_membership:
        return existing_membership

    new_membership = ProjectMemberModel(project_id=project.id, user_id=user.id)
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    return new_membership


def remove_project_member_from_db(
    db: Session, project_id: uuid.UUID, member_in: ProjectMemberAdd
) -> None:
    project = get_project_from_db(db, project_id)
    user = db.get(UserModel, member_in.user_id)

    if not user:
        raise UserNotFoundException(f"User with ID '{member_in.user_id}' not found.")

    existing_membership = db.get(ProjectMemberModel, (project.id, user.id))
    if not existing_membership:
        raise MemberRemovalError(f"Member with ID '{member_in.user_id}' is not part of project with ID '{project_id}'.")

    db.delete(existing_membership)
    db.commit()


#Improvement: apply join 
def list_project_members_from_db(db: Session, project_id: uuid.UUID) -> list[UserModel]:
    results = (db.query(UserModel)
        .join(ProjectMemberModel, UserModel.id == ProjectMemberModel.user_id)
        .filter(ProjectMemberModel.project_id == project_id).all())
    return results
    
    
