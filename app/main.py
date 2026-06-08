from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.routers import project_router, user_router, task_router
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException, TaskNotFoundException, ProjectNotFoundException 


settings = get_settings()


api = FastAPI(title=settings.app_name, debug=settings.debug)
api.include_router(user_router)
api.include_router(project_router)
api.include_router(task_router)


@api.get("/")
async def root():
    return {"status": "ok", "app": settings.app_name}

@api.exception_handler(OperationalError)
async def database_operational_exception_handler(request: Request, exc: OperationalError):
    print(f"Database connection error: {exc}") #for debugging purposes
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database connection error. Please try again later."}
    )

@api.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@api.exception_handler(UserAlreadyExistsException)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@api.exception_handler(TaskNotFoundException)
async def task_not_found_handler(request: Request, exc: TaskNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@api.exception_handler(ProjectNotFoundException)
async def project_not_found_handler(request: Request, exc: ProjectNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:api", reload=True)
