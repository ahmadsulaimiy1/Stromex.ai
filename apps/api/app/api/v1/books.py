import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.core.pagination import Page, pagination
from app.db.base import get_db
from app.db.models.book import Book, BookChapter
from app.db.models.user import User
from app.schemas.book import (
    BookCreate,
    BookRead,
    BookWithChapters,
    ChapterCreate,
    ChapterRead,
    ChapterUpdate,
)
from app.services.pdf_service import render_book_pdf

router = APIRouter(prefix="/books", tags=["books"])


def _get_owned_book(db: Session, user: User, book_id: uuid.UUID, *, with_chapters: bool = False) -> Book:
    query = db.query(Book)
    if with_chapters:
        query = query.options(selectinload(Book.chapters))
    book = query.filter(Book.id == book_id).first()
    if book is None or book.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Book:
    book = Book(user_id=user.id, **payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.get("", response_model=list[BookRead])
def list_books(
    page: Page = Depends(pagination),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Book]:
    return (
        db.query(Book)
        .filter(Book.user_id == user.id)
        .order_by(Book.updated_at.desc())
        .offset(page.offset)
        .limit(page.limit)
        .all()
    )


@router.get("/{book_id}", response_model=BookWithChapters)
def get_book(
    book_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Book:
    return _get_owned_book(db, user, book_id, with_chapters=True)


_MAX_CHAPTERS_PER_BOOK = 300  # generous for any real book; a real, enforced ceiling


@router.post("/{book_id}/chapters", response_model=ChapterRead, status_code=status.HTTP_201_CREATED)
def create_chapter(
    book_id: uuid.UUID,
    payload: ChapterCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookChapter:
    _get_owned_book(db, user, book_id)

    existing_count = db.query(func.count(BookChapter.id)).filter(BookChapter.book_id == book_id).scalar()
    if existing_count >= _MAX_CHAPTERS_PER_BOOK:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A book may have at most {_MAX_CHAPTERS_PER_BOOK} chapters.",
        )

    chapter = BookChapter(book_id=book_id, **payload.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.patch("/{book_id}/chapters/{chapter_id}", response_model=ChapterRead)
def update_chapter(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    payload: ChapterUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookChapter:
    _get_owned_book(db, user, book_id)
    chapter = db.get(BookChapter, chapter_id)
    if chapter is None or chapter.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chapter, field, value)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.get("/{book_id}/export.pdf")
def export_book_pdf(
    book_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Response:
    book = _get_owned_book(db, user, book_id, with_chapters=True)
    pdf_bytes = render_book_pdf(book)
    filename = "".join(c for c in book.title if c.isalnum() or c in " -_").strip() or "book"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )
