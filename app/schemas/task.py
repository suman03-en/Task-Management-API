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

class TaskCreateData(TaskBase):
    project_id: uuid.UUID
    
class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: uuid.UUID | None = None

class TaskRequestRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    request_by: uuid.UUID
    request_at: datetime

class TaskRequestCreate(BaseModel):
    task_id: uuid.UUID


