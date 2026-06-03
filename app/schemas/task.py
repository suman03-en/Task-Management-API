import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TaskBase(BaseModel):
    name: str
    description: str | None = None
    project_id: uuid.UUID

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None  


class TaskListResponse(BaseModel):
    tasks: list[TaskRead]
    count: int = 0


