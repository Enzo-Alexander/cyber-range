"""用户相关路由。"""
from calendar import monthrange
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Challenge, CompetitionSolve, Favorite, SolveRecord, User
from ..security import hash_password, verify_password
from ..schemas import (
    AccountUpdateIn,
    CategoryProgress,
    DailyActivity,
    FavoriteChallengeOut,
    FavoriteState,
    MonthlyActivityOut,
    PasswordChangeIn,
    ProfileOut,
    ProfileSolve,
    UserOut,
    YearlyActivityOut,
    YearlyMonthActivity,
)

router = APIRouter(prefix="/users", tags=["users"])

CATEGORIES = ["逆向工程", "二进制漏洞", "密码学", "Web安全", "流量分析", "数字取证"]
LEVEL_STEP = 5


def _local_solve_times(
    db: Session,
    user_id: int,
    start_utc: datetime,
    end_utc: datetime,
) -> list[datetime]:
    """返回指定 UTC 区间内、转换为北京时间后的解题时间。"""
    regular_times = (
        db.query(SolveRecord.solved_at)
        .filter(
            SolveRecord.user_id == user_id,
            SolveRecord.solved_at >= start_utc,
            SolveRecord.solved_at < end_utc,
        )
        .all()
    )
    competition_times = (
        db.query(CompetitionSolve.solved_at)
        .filter(
            CompetitionSolve.user_id == user_id,
            CompetitionSolve.solved_at >= start_utc,
            CompetitionSolve.solved_at < end_utc,
        )
        .all()
    )
    return [
        solved_at + timedelta(hours=8)
        for (solved_at,) in regular_times + competition_times
    ]


@router.get("/me", response_model=UserOut)
def read_me(current: User = Depends(get_current_user)):
    return current


@router.patch("/me/account", response_model=UserOut)
def update_my_account(
    body: AccountUpdateIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.email != current.email:
        exists = (
            db.query(User)
            .filter(User.email == body.email, User.id != current.id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="该邮箱已被其他账号使用")
        current.email = body.email
        db.commit()
        db.refresh(current)
    return current


@router.post("/me/change-password")
def change_my_password(
    body: PasswordChangeIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, current.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    current.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"success": True}


@router.get("/me/favorites", response_model=list[FavoriteChallengeOut])
def my_favorites(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Favorite, Challenge)
        .join(Challenge, Challenge.id == Favorite.challenge_id)
        .filter(
            Favorite.user_id == current.id,
            Challenge.status == "published",
        )
        .order_by(Favorite.created_at.desc())
        .all()
    )
    solved_ids = {
        solve.challenge_id
        for solve in db.query(SolveRecord)
        .filter(SolveRecord.user_id == current.id)
        .all()
    }
    return [
        FavoriteChallengeOut(
            id=challenge.id,
            title=challenge.title,
            category=challenge.category,
            difficulty=challenge.difficulty,
            points=challenge.points,
            status=challenge.status,
            solved_count=challenge.solved_count,
            solved_by_me=challenge.id in solved_ids,
            favorited_at=favorite.created_at,
        )
        for favorite, challenge in rows
    ]


@router.post("/me/favorites/{challenge_id}/toggle", response_model=FavoriteState)
def toggle_favorite(
    challenge_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = db.get(Challenge, challenge_id)
    if challenge is None or challenge.status != "published":
        raise HTTPException(status_code=404, detail="题目不存在或未上架")

    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current.id,
            Favorite.challenge_id == challenge_id,
        )
        .first()
    )
    if favorite:
        db.delete(favorite)
        favorited = False
    else:
        db.add(Favorite(user_id=current.id, challenge_id=challenge_id))
        favorited = True
    db.commit()
    return FavoriteState(favorited=favorited)


@router.get("/me/activity/monthly", response_model=MonthlyActivityOut)
def monthly_activity(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """按北京时间统计某月每天的解题数量（题库 + 比赛真题）。"""
    days = monthrange(year, month)[1]
    start_local = datetime(year, month, 1)
    if month == 12:
        next_local = datetime(year + 1, 1, 1)
    else:
        next_local = datetime(year, month + 1, 1)

    # 中国标准时间固定为 UTC+8，避免依赖 Windows 上的 IANA 时区数据。
    start_utc = start_local - timedelta(hours=8)
    end_utc = next_local - timedelta(hours=8)

    counts = [0] * days
    for local_time in _local_solve_times(db, current.id, start_utc, end_utc):
        counts[local_time.day - 1] += 1

    return MonthlyActivityOut(
        year=year,
        month=month,
        days=days,
        total=sum(counts),
        active_days=sum(1 for count in counts if count > 0),
        daily=[
            DailyActivity(day=index + 1, count=count)
            for index, count in enumerate(counts)
        ],
    )


@router.get("/me/activity/yearly", response_model=YearlyActivityOut)
def yearly_activity(
    year: int = Query(ge=2000, le=2100),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """按北京时间统计整年每天的解题数量（题库 + 比赛真题）。"""
    start_utc = datetime(year, 1, 1) - timedelta(hours=8)
    end_utc = datetime(year + 1, 1, 1) - timedelta(hours=8)

    month_counts: dict[int, list[int]] = {
        month: [0] * monthrange(year, month)[1]
        for month in range(1, 13)
    }
    for local_time in _local_solve_times(db, current.id, start_utc, end_utc):
        month_counts[local_time.month][local_time.day - 1] += 1

    months = [
        YearlyMonthActivity(
            month=month,
            days=len(counts),
            total=sum(counts),
            daily=[
                DailyActivity(day=index + 1, count=count)
                for index, count in enumerate(counts)
            ],
        )
        for month, counts in month_counts.items()
    ]
    return YearlyActivityOut(
        year=year,
        total=sum(month.total for month in months),
        active_days=sum(
            1
            for month in months
            for item in month.daily
            if item.count > 0
        ),
        months=months,
    )


@router.get("/me/profile", response_model=ProfileOut)
def my_profile(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    solves = (
        db.query(SolveRecord)
        .filter(SolveRecord.user_id == current.id)
        .order_by(SolveRecord.solved_at.desc())
        .all()
    )
    ch_map = {c.id: c for c in db.query(Challenge).all()}

    total_points = sum(s.points for s in solves)
    total_solved = len(solves)
    competition_solved = (
        db.query(CompetitionSolve)
        .filter(CompetitionSolve.user_id == current.id)
        .count()
    )
    level_total_solved = total_solved + competition_solved
    level = level_total_solved // LEVEL_STEP + 1
    level_progress = level_total_solved % LEVEL_STEP

    # 排名：按总分降序，统计高于当前用户的人数 + 1
    agg = (
        db.query(
            SolveRecord.user_id,
            func.sum(SolveRecord.points).label("total"),
        )
        .group_by(SolveRecord.user_id)
        .all()
    )
    better = sum(1 for _, t in agg if int(t) > total_points)
    rank = better + 1 if total_solved else 0

    # 掌握度：每分类已解题目 / 该分类已上架题目
    published = db.query(Challenge).filter(Challenge.status == "published").all()
    per_cat_total: dict[str, int] = {}
    for c in published:
        per_cat_total[c.category] = per_cat_total.get(c.category, 0) + 1
    solved_cat: dict[str, int] = {}
    for s in solves:
        c = ch_map.get(s.challenge_id)
        if c:
            solved_cat[c.category] = solved_cat.get(c.category, 0) + 1

    progress = [
        CategoryProgress(
            category=cat,
            percent=round(solved_cat.get(cat, 0) / per_cat_total.get(cat, 1) * 100) if per_cat_total.get(cat) else 0,
        )
        for cat in CATEGORIES
    ]

    profile_solves: list[ProfileSolve] = []
    for s in solves:
        c = ch_map.get(s.challenge_id)
        if not c:
            continue
        profile_solves.append(
            ProfileSolve(
                challenge_id=c.id,
                title=c.title,
                category=c.category,
                points=s.points,
                solved_at=s.solved_at,
            )
        )

    return ProfileOut(
        user=UserOut.model_validate(current),
        total_points=total_points,
        total_solved=total_solved,
        competition_solved=competition_solved,
        level=level,
        level_progress=level_progress,
        level_required=LEVEL_STEP,
        rank=rank,
        progress=progress,
        solves=profile_solves,
    )
