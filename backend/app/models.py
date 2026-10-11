"""数据模型。"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    solves: Mapped[list["SolveRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Challenge(Base):
    """题目模型。"""

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5 星
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    attachment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    flag: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="published", nullable=False)  # published/pending/draft
    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    solves: Mapped[list["SolveRecord"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class SolveRecord(Base):
    """解题记录。"""

    __tablename__ = "solve_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), index=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="solves")
    challenge: Mapped["Challenge"] = relationship(back_populates="solves")
