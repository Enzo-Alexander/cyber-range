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


class AccountUpdateIn(BaseModel):
    email: EmailStr


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


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


class ChallengeSubmitIn(BaseModel):
    """普通用户提交题目：状态由服务端固定为待审核。"""

    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    difficulty: int = Field(ge=1, le=5, default=1)
    points: int = Field(ge=0, default=100)
    description: str = ""
    attachment: str | None = None
    flag: str = Field(min_length=1, max_length=255)


class ChallengeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    points: int | None = Field(default=None, ge=0)
    description: str | None = None
    attachment: str | None = None
    flag: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, pattern="^(published|pending|draft|rejected)$")


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
    favorited_by_me: bool = False


class AdminChallengeOut(ChallengeOut):
    """管理员视图：包含 Flag，便于审核。"""

    flag: str


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


class FavoriteChallengeOut(ChallengeCard):
    favorited_at: datetime


class FavoriteState(BaseModel):
    favorited: bool


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


class DailyActivity(BaseModel):
    day: int
    count: int


class MonthlyActivityOut(BaseModel):
    year: int
    month: int
    days: int
    total: int
    active_days: int
    daily: list[DailyActivity]


class YearlyMonthActivity(BaseModel):
    month: int
    days: int
    total: int
    daily: list[DailyActivity]


class YearlyActivityOut(BaseModel):
    year: int
    total: int
    active_days: int
    months: list[YearlyMonthActivity]


class ProfileOut(BaseModel):
    user: UserOut
    total_points: int
    total_solved: int
    competition_solved: int = 0
    level: int
    level_progress: int
    level_required: int
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


# ---------- 通知 ----------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    content: str
    related_challenge_id: int | None
    related_article_id: int | None
    is_read: bool
    created_at: datetime


# ---------- 比赛 / 真题 ----------
class CompetitionIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    icon: str = "🏆"


class CompetitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    icon: str
    created_at: datetime


class CompetitionEditionIn(BaseModel):
    competition_id: int
    name: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=2000, le=2100)


class CompetitionEditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    competition_id: int
    name: str
    year: int
    created_at: datetime
    # 当前用户在该届比赛里已获得的分数
    my_points: int = 0


class CompetitionChallengeIn(BaseModel):
    edition_id: int
    title: str = Field(min_length=1, max_length=200)
    category: str = "Web"
    difficulty: int = Field(ge=1, le=5, default=1)
    points: int = Field(ge=0, le=100000, default=100)
    description: str = ""
    flag: str = ""
    attachment: str | None = None


class CompetitionChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    edition_id: int
    title: str
    category: str
    difficulty: int
    description: str
    points: int = 100
    solved_count: int = 0
    solved_by_me: bool = False
    attachment: str | None = None
    created_at: datetime


class CompetitionChallengeDetailOut(BaseModel):
    """比赛题目详情：附带所属比赛与届次信息，供详情页展示。

    刻意不含 flag 字段，避免把答案下发到浏览器（flag 由后端校验）。
    """

    id: int
    edition_id: int
    title: str
    category: str
    difficulty: int
    description: str
    attachment: str | None = None
    created_at: datetime
    points: int = 100
    solved_count: int = 0
    solved_by_me: bool = False
    competition_id: int
    competition_name: str
    competition_icon: str
    edition_name: str
    edition_year: int
