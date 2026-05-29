from contextlib import asynccontextmanager
from fastapi import FastAPI

from .core.config import get_settings
from .db.init_db import init_db
from .routers import project_router, user_router

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
