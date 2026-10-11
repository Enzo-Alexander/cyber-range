"""CyberRange 后端入口。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth, challenges, users
from .seed import init_db

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(challenges.router, prefix=settings.api_prefix)
app.include_router(challenges.admin_router, prefix=settings.api_prefix)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name}
