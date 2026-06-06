from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=5000)


class ProjectCreate(ProjectBase):
    owner_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=5000)
    owner_id: Optional[UUID] = None


class ProjectRead(ProjectBase):
    id: UUID
    owner_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectMemberAdd(BaseModel):
    user_id: UUID

class ProjectMemberRead(BaseModel):
    user_id: UUID
    project_id: UUID
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectMemberListResponse(BaseModel):
    members: list[ProjectMemberRead]
