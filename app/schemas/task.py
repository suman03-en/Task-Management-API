from pydantic import BaseModel, ConfigDict

class TaskBase(BaseModel):
    name: str
    description: str | None = None
    project_id: str

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str
    updated_at: str


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None  


