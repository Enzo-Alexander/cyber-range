"""图书馆书籍与页面管理。"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_role
from ..models import Book, BookPage, User
from ..schemas import (
    BookDetailOut,
    BookIn,
    BookOut,
    BookPageIn,
    BookPageOut,
    BookPageUpdate,
    BookUpdate,
)

router = APIRouter(prefix="/books", tags=["books"])
admin_router = APIRouter(prefix="/admin/books", tags=["admin-books"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "books")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _book_out(book: Book) -> BookOut:
    return BookOut(
        id=book.id,
        title=book.title,
        author=book.author,
        page_count=len(book.pages),
        created_at=book.created_at,
    )


def _book_detail(book: Book) -> BookDetailOut:
    return BookDetailOut(
        id=book.id,
        title=book.title,
        author=book.author,
        created_at=book.created_at,
        pages=[BookPageOut.model_validate(page) for page in book.pages],
    )


def _get_book(db: Session, book_id: int) -> Book:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book


@router.get("", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)):
    books = db.query(Book).order_by(Book.created_at.desc()).all()
    return [_book_out(book) for book in books]


@router.get("/{book_id}", response_model=BookDetailOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return _book_detail(_get_book(db, book_id))


@admin_router.get("", response_model=list[BookOut])
def admin_list_books(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    books = db.query(Book).order_by(Book.created_at.desc()).all()
    return [_book_out(book) for book in books]


@admin_router.post("", response_model=BookDetailOut, status_code=201)
def create_book(
    payload: BookIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    book = Book(title=payload.title.strip(), author=admin.username)
    db.add(book)
    db.flush()
    db.add(BookPage(book_id=book.id, position=1, content=""))
    db.commit()
    db.refresh(book)
    return _book_detail(book)


@admin_router.put("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    payload: BookUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    book = _get_book(db, book_id)
    book.title = payload.title.strip()
    db.commit()
    db.refresh(book)
    return _book_out(book)


@admin_router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    book = _get_book(db, book_id)
    db.delete(book)
    db.commit()


@admin_router.post("/{book_id}/pages", response_model=BookDetailOut, status_code=201)
def add_book_page(
    book_id: int,
    payload: BookPageIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    book = _get_book(db, book_id)
    position = (max((page.position for page in book.pages), default=0) + 1)

    if payload.after_page_id is not None:
        anchor = next(
            (page for page in book.pages if page.id == payload.after_page_id),
            None,
        )
        if not anchor:
            raise HTTPException(status_code=404, detail="插入位置页面不存在")
        position = anchor.position + 1
        for page in book.pages:
            if page.position >= position:
                page.position += 1

    db.add(BookPage(
        book_id=book.id,
        position=position,
        content=payload.content,
        image=payload.image,
    ))
    db.commit()
    db.refresh(book)
    return _book_detail(book)


@admin_router.put("/{book_id}/pages/{page_id}", response_model=BookDetailOut)
def update_book_page(
    book_id: int,
    page_id: int,
    payload: BookPageUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    book = _get_book(db, book_id)
    page = db.query(BookPage).filter(
        BookPage.id == page_id,
        BookPage.book_id == book.id,
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    page.content = payload.content
    page.image = payload.image
    db.commit()
    db.refresh(book)
    return _book_detail(book)


@admin_router.delete("/{book_id}/pages/{page_id}", response_model=BookDetailOut)
def delete_book_page(
    book_id: int,
    page_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    book = _get_book(db, book_id)
    if len(book.pages) <= 1:
        raise HTTPException(status_code=400, detail="书籍至少需要保留一页")

    page = next((item for item in book.pages if item.id == page_id), None)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    db.delete(page)
    db.flush()
    remaining = db.query(BookPage).filter(
        BookPage.book_id == book.id,
    ).order_by(BookPage.position).all()
    for index, item in enumerate(remaining, start=1):
        item.position = index
    db.commit()
    db.expire_all()
    db.refresh(book)
    return _book_detail(book)


@admin_router.post("/upload-image")
async def upload_book_image(
    file: UploadFile = File(...),
    _admin: User = Depends(require_role("admin")),
):
    allowed = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    extension = allowed.get(file.content_type or "")
    if not extension:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 和 GIF 图片")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")

    name = f"{uuid.uuid4().hex}.{extension}"
    with open(os.path.join(UPLOAD_DIR, name), "wb") as output:
        output.write(data)
    return {"path": f"/api/uploads/books/{name}"}
