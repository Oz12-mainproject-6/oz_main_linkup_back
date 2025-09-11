from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.config import TORTOISE_ORM


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=True,
    )
    yield
    # Shutdown
    pass


app = FastAPI(
    title="OZ LinkUp Backend",
    description="OZ LinkUp 백엔드 API",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}