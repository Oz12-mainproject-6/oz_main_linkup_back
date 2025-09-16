from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from app.config import TORTOISE_ORM
from app.features.users.router import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    # Shutdown
    await Tortoise.close_connections()


app = FastAPI(
    title="OZ LinkUp Backend",
    description="OZ LinkUp 백엔드 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 라우터 등록
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
