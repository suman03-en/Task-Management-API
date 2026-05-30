from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import get_settings
import app.models
from app.db.database import init_db
from app.routers import project_router, user_router

settings = get_settings()


@asynccontextmanager
async def lifespan(api: FastAPI):
    init_db()
    yield


api = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
api.include_router(user_router)
api.include_router(project_router)


@api.get("/")
async def root():
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:api", reload=True)
