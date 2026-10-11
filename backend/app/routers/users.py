"""用户相关路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Challenge, SolveRecord, User
from ..schemas import CategoryProgress, ProfileOut, ProfileSolve, UserOut

router = APIRouter(prefix="/users", tags=["users"])

CATEGORIES = ["逆向工程", "二进制漏洞", "密码学", "Web安全", "流量分析", "数字取证"]


@router.get("/me", response_model=UserOut)
def read_me(current: User = Depends(get_current_user)):
    return current


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
        rank=rank,
        progress=progress,
        solves=profile_solves,
    )
