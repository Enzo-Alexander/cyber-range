"""文章 / 公告接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_role
from ..models import Article
from ..schemas import ArticleIn, ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])
admin_router = APIRouter(prefix="/admin/articles", tags=["admin-articles"])


@router.get("", response_model=list[ArticleOut])
def list_articles(db: Session = Depends(get_db)):
    rows = db.query(Article).order_by(Article.created_at.desc()).all()
    return rows


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        from fastapi import HTTPException
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
    db.commit()
    db.refresh(art)
    return art
