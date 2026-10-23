"""文章 / 公告接口。"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_role
from ..models import Article, Notification, User
from ..schemas import ArticleIn, ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])
admin_router = APIRouter(prefix="/admin/articles", tags=["admin-articles"])


@router.get("", response_model=list[ArticleOut])
def list_articles(
    article_type: Literal["article", "announcement"] | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
):
    query = db.query(Article)
    if article_type:
        query = query.filter(Article.type == article_type)
    rows = query.order_by(Article.created_at.desc()).all()
    return rows


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="文章不存在")
    return art


@admin_router.post("", response_model=ArticleOut)
def create_article(
    body: ArticleIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    art = Article(title=body.title, content=body.content, type=body.type)
    db.add(art)
    db.flush()
    if body.type == "announcement":
        recipients = (
            db.query(User)
            .filter(User.role == "user", User.is_active.is_(True))
            .all()
        )
        for user in recipients:
            db.add(
                Notification(
                    user_id=user.id,
                    type="announcement_published",
                    title=f"新公告：{art.title}",
                    content=f"管理员发布了新公告《{art.title}》，点击查看。",
                    related_article_id=art.id,
                )
            )
    db.commit()
    db.refresh(art)
    return art


@admin_router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    art = db.get(Article, article_id)
    if art is None:
        raise HTTPException(status_code=404, detail="公告或文章不存在")
    db.query(Notification).filter(
        Notification.related_article_id == article_id
    ).delete(synchronize_session=False)
    db.delete(art)
    db.commit()
    return {"success": True}
