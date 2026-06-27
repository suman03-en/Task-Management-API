import uuid

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.models.project import Project as ProjectModel
from app.models.project import ProjectMember as ProjectMemberModel
from app.models.user import User as UserModel
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberAdd
from app.core.exceptions import (
    ProjectNotFoundException,
    UserNotFoundException,
    MemberRemovalError,
    MemberAdditionError,
    PermissionDeniedException,
)


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project_in: ProjectCreate, current_user: UserModel) -> ProjectModel:
        project_db = ProjectModel(**project_in.model_dump(), owner_id=current_user.id)
        self.db.add(project_db)
        self.db.flush()
        membership = ProjectMemberModel(project_id=project_db.id, user_id=current_user.id, role="creator")
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(project_db)
        return project_db

    def list_projects(self, current_user: UserModel, offset: int = 0, limit: int = 20) -> tuple[list[ProjectModel], int]:
        base_query = (
        select(ProjectModel)
        .outerjoin(ProjectModel.members)
        .where(
            or_(
                ProjectModel.owner_id == current_user.id,
                ProjectMemberModel.user_id == current_user.id
            )
        )
        .distinct()
    )
    
        total = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        projects = list(self.db.scalars(base_query.offset(offset).limit(limit)).all())
        
        return projects, total
    
    def get_project(self, project_id: uuid.UUID) -> ProjectModel:
        project = self.db.get(ProjectModel, project_id)
        if project is None:
            raise ProjectNotFoundException(f"Project with ID '{project_id}' not found.")
        return project

    def update_project(self, project_id: uuid.UUID, project_in: ProjectUpdate) -> ProjectModel:
        project_db = self.get_project(project_id)

        for field, value in project_in.model_dump(exclude_unset=True).items():
            setattr(project_db, field, value)

        self.db.commit()
        self.db.refresh(project_db)
        return project_db
    
    def delete_project(self, project_id: uuid.UUID, current_user: UserModel) -> None:
        project = self.get_project(project_id)
        if project.owner_id != current_user.id:
            raise PermissionDeniedException("Only the project owner can delete this project.")
        self.db.delete(project)
        self.db.commit()

    def add_project_member(self, project_id: uuid.UUID, member_in: ProjectMemberAdd) -> ProjectMemberModel:
        project = self.get_project(project_id)
        user = self.db.get(UserModel, member_in.user_id)
        if not user:
            raise UserNotFoundException(f"User with ID '{member_in.user_id}' not found.")

        existing_membership = self.db.get(ProjectMemberModel, (project.id, user.id))
        if existing_membership:
            raise MemberAdditionError(f"User '{member_in.user_id}' is already a member of this project.")

        new_membership = ProjectMemberModel(project_id=project.id, user_id=user.id)
        self.db.add(new_membership)
        self.db.commit()
        self.db.refresh(new_membership)
        return new_membership

    def remove_project_member(self, project_id: uuid.UUID, user_id: uuid.UUID, current_user: UserModel) -> None:
        project = self.get_project(project_id)
        user = self.db.get(UserModel, user_id)

        if not user:
            raise UserNotFoundException(f"User with ID '{user_id}' not found.")

        existing_membership = self.db.get(ProjectMemberModel, (project.id, user.id))
        if not existing_membership:
            raise MemberRemovalError(f"Member with ID '{user_id}' is not part of project with ID '{project_id}'.")

        self.db.delete(existing_membership)
        self.db.commit()

    def list_project_members(self, project_id: uuid.UUID) -> list[UserModel]:
        members = (
            self.db.query(UserModel)
            .join(ProjectMemberModel, UserModel.id == ProjectMemberModel.user_id)
            .filter(ProjectMemberModel.project_id == project_id)
            .all()
        )
        return members

    def is_user_project_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        membership = self.db.get(ProjectMemberModel, (project_id, user_id))
        return membership is not None

