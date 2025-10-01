import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from tortoise import Tortoise

from app.config import TORTOISE_ORM
from app.features.artists.router import idol_router
from app.features.companies.router import companies_router
from app.features.events.routers import event_router
from app.features.posts.router import posts_router
from app.features.subscriptions.router import subscriptions_router
from app.features.superuser.router import superuser_router
from app.features.uploads.router import uploads_router
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

# CORS 설정 - 개발 환경에서는 모든 도메인 허용

# 개발 환경에서는 모든 출처 허용
if os.getenv("ENVIRONMENT") == "production":
    # 프로덕션에서는 특정 도메인만 허용
    origins = [
        "https://dev.linkup.n-e.kr",
        "http://localhost:5173",
        os.getenv("FRONTEND_DOMAIN", ""),
    ]
    allow_credentials = True
else:
    # 개발 환경에서는 광범위하게 허용
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:4173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:4173",
        "null",  # 파일에서 직접 열기
    ]
    allow_credentials = False  # 개발 환경에서는 credentials 비활성화

# CORS 설정 - 환경별 도메인 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 위에서 정의한 origins 사용
    allow_credentials=allow_credentials,  # 환경별 credentials 설정
    allow_methods=["*"],  # 모든 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
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
# 포스트 라우터 등록
app.include_router(posts_router)
# 업로드 라우터 등록
app.include_router(uploads_router)
# 슈퍼유저 라우터 등록
app.include_router(superuser_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
