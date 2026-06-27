"""
All dependency functions of service classes are defined here. These functions are used to inject service instances into FastAPI endpoints.
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from app.services.user import UserService
from app.services.project import ProjectService
from app.services.task import TaskService
from app.dependencies.db import get_db

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)

def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)
