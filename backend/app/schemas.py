"""Pydantic 校验模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- 认证 ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


# ---------- 题目 ----------
class ChallengeIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    difficulty: int = Field(ge=1, le=5, default=1)
    points: int = Field(ge=0, default=100)
    description: str = ""
    attachment: str | None = None
    flag: str = Field(min_length=1, max_length=255)
    status: str = Field(default="published", pattern="^(published|pending|draft)$")


class ChallengeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    points: int | None = Field(default=None, ge=0)
    description: str | None = None
    attachment: str | None = None
    flag: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, pattern="^(published|pending|draft)$")


class ChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    difficulty: int
    points: int
    description: str
    attachment: str | None
    author: str
    status: str
    solved_count: int
    created_at: datetime


class ChallengeCard(BaseModel):
    """题库卡片（列表用，不带 description/flag）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    difficulty: int
    points: int
    status: str
    solved_count: int
    solved_by_me: bool = False


class SolveIn(BaseModel):
    flag: str = Field(min_length=1, max_length=512)


class SolveOut(BaseModel):
    success: bool
    message: str
    points: int = 0


class SolverOut(BaseModel):
    username: str
    solved_at: datetime


# ---------- 排行榜 / 个人 ----------
class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    total_points: int
    solved_count: int
    last_solved_at: datetime | None


class ProfileSolve(BaseModel):
    challenge_id: int
    title: str
    category: str
    points: int
    solved_at: datetime


class CategoryProgress(BaseModel):
    category: str
    percent: int  # 0-100 掌握度


class ProfileOut(BaseModel):
    user: UserOut
    total_points: int
    total_solved: int
    rank: int
    progress: list[CategoryProgress]
    solves: list[ProfileSolve]


# ---------- 文章 / 公告 ----------
class ArticleIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="")
    type: str = Field(default="article", pattern="^(article|announcement)$")


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    type: str
    author: str
    created_at: datetime
