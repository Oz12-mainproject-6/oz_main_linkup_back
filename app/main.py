from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.security import HTTPBearer
from tortoise import Tortoise

from app.config import TORTOISE_ORM

from app.features.events.routers import event_router

from app.features.artists.router import idol_router
from app.features.companies.router import companies_router
from app.features.subscriptions.router import subscriptions_router

from app.features.users.router import auth_router

from fastapi.middleware.cors import CORSMiddleware

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

# React 쪽 도메인 등록 (개발/배포 환경에 맞게 바꾸기)
import os

origins = [
    "http://localhost:3000",    # React 기본 포트
    "http://localhost:5173",    # Vite 기본 포트
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# 배포 환경에서 도메인 추가
if os.getenv("ENVIRONMENT") == "production":
    frontend_domain = os.getenv("FRONTEND_DOMAIN")
    if frontend_domain:
        origins.append(frontend_domain)
else:
    # 개발 환경에서는 모든 localhost 허용
    origins.extend([
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ])

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 허용할 출처
    allow_credentials=True,
    allow_methods=["*"],        # GET, POST, PUT, DELETE 등 모두 허용
    allow_headers=["*"],        # 모든 헤더 허용
)

# Swagger UI에서 Bearer 토큰 인증 설정
security = HTTPBearer()

# 계정 라우터 등록
app.include_router(auth_router)
# 일정 라우터 등록
app.include_router(event_router)
# 아티스트 라우터 등록
app.include_router(idol_router)
# 소속사 라우터 등록
app.include_router(companies_router)
# 구독 라우터 등록
app.include_router(subscriptions_router)



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
