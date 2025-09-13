from fastapi import APIRouter

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


@auth_router.post("/signup")
async def signup():
    return {"message": "signup endpoint"}


@auth_router.post("/login")
async def login():
    return {"message": "login endpoint"}


@auth_router.post("/logout")
async def logout():
    return {"message": "logout endpoint"}