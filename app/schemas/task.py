import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.core.constants import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    name: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: uuid.UUID | None = None

class TaskCreate(TaskBase):
    pass

class TaskInDB(TaskBase):
    project_id: uuid.UUID
    
class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: uuid.UUID | None = None


class TaskListResponse(BaseModel):
    tasks: list[TaskRead]
    count: int = 0


