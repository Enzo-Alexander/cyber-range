"""CyberRange 后端入口。"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import articles, auth, challenges, competitions, notifications, parse_doc, traffic, users
from .seed import init_db

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 uploads 静态目录（文章图片等）
_uploads_root = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(_uploads_root, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_root), name="uploads")


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(challenges.router, prefix=settings.api_prefix)
app.include_router(challenges.admin_router, prefix=settings.api_prefix)
app.include_router(articles.router, prefix=settings.api_prefix)
app.include_router(articles.admin_router, prefix=settings.api_prefix)
app.include_router(notifications.router, prefix=settings.api_prefix)
app.include_router(parse_doc.router, prefix=settings.api_prefix)
app.include_router(traffic.router, prefix=settings.api_prefix)
app.include_router(competitions.router, prefix=settings.api_prefix)
app.include_router(competitions.admin_router, prefix=settings.api_prefix)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name}
