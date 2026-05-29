from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import get_settings
from app.db.database import init_db
from app.routers import project_router, user_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(user_router)
app.include_router(project_router)


@app.get("/")
async def root():
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
