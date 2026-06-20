from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    role_id: UUID | None = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserBase):
    hashed_password: str

class ProjectMember(BaseModel):
    members: list[UserRead]


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str



