import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.routers import project_router, user_router, task_router
from app.core.exceptions import (
    AppBaseException,
    UserAlreadyExistsException,
    UserNotFoundException,
    TaskNotFoundException,
    ProjectNotFoundException,
    MemberAdditionError,
    MemberRemovalError,
    PermissionDeniedException,
)
from app.bootstrap.roles import load_roles

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(api: FastAPI):
    # startup
    logger.info("Application startup: validating database connection...")
    load_roles()
    yield
    # shutdown
    logger.info("Application shutdown.")


api = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

# Register routers with API version prefix
api.include_router(user_router, prefix="/api/v1")
api.include_router(project_router, prefix="/api/v1")
api.include_router(task_router, prefix="/api/v1")


@api.get("/")
async def root():
    return {"status": "ok", "app": settings.app_name}


@api.exception_handler(OperationalError)
async def database_operational_exception_handler(request: Request, exc: OperationalError):
    logger.error("Database connection error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database connection error. Please try again later."}
    )


@api.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    """Generic exception handler for all application-level custom exceptions."""
    status_map = {
        UserAlreadyExistsException: status.HTTP_409_CONFLICT,
        UserNotFoundException: status.HTTP_404_NOT_FOUND,
        TaskNotFoundException: status.HTTP_404_NOT_FOUND,
        ProjectNotFoundException: status.HTTP_404_NOT_FOUND,
        MemberAdditionError: status.HTTP_409_CONFLICT,
        MemberRemovalError: status.HTTP_400_BAD_REQUEST,
        PermissionDeniedException: status.HTTP_403_FORBIDDEN,
    }
    status_code = status_map.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:api", reload=True)
