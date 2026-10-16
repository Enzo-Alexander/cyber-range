"""比赛 / 真题接口。"""
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, get_current_user_optional, require_role
from ..models import (
    Competition,
    CompetitionChallenge,
    CompetitionEdition,
    CompetitionSolve,
    User,
)
from ..security import verify_password
from ..schemas import (
    CompetitionChallengeIn,
    CompetitionChallengeOut,
    CompetitionChallengeDetailOut,
    CompetitionEditionIn,
    CompetitionEditionOut,
    CompetitionIn,
    CompetitionOut,
    SolveIn,
    SolveOut,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])
admin_router = APIRouter(prefix="/admin/competitions", tags=["admin-competitions"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


def _solved_ids(db: Session, user: User | None, challenge_ids: list[int]) -> set[int]:
    """当前用户在这些比赛题目里已经解出的那些。"""
    if user is None or not challenge_ids:
        return set()
    rows = (
        db.query(CompetitionSolve.challenge_id)
        .filter(
            CompetitionSolve.user_id == user.id,
            CompetitionSolve.challenge_id.in_(challenge_ids),
        )
        .all()
    )
    return {row[0] for row in rows}


def _edition_points(db: Session, user: User | None, edition_ids: list[int]) -> dict[int, int]:
    """当前用户在各届比赛里已获得的分数。"""
    if user is None or not edition_ids:
        return {}
    rows = (
        db.query(
            CompetitionChallenge.edition_id,
            func.coalesce(func.sum(CompetitionSolve.points), 0),
        )
        .join(CompetitionSolve, CompetitionSolve.challenge_id == CompetitionChallenge.id)
        .filter(
            CompetitionChallenge.edition_id.in_(edition_ids),
            CompetitionSolve.user_id == user.id,
        )
        .group_by(CompetitionChallenge.edition_id)
        .all()
    )
    return {int(edition_id): int(total) for edition_id, total in rows}


def _detail(
    ch: CompetitionChallenge, db: Session, user: User | None = None
) -> CompetitionChallengeDetailOut:
    edition = db.get(CompetitionEdition, ch.edition_id)
    comp = db.get(Competition, edition.competition_id) if edition else None
    return CompetitionChallengeDetailOut(
        id=ch.id,
        edition_id=ch.edition_id,
        title=ch.title,
        category=ch.category,
        difficulty=ch.difficulty,
        description=ch.description,
        attachment=ch.attachment,
        created_at=ch.created_at,
        points=ch.points,
        solved_count=ch.solved_count,
        solved_by_me=ch.id in _solved_ids(db, user, [ch.id]),
        competition_id=comp.id if comp else 0,
        competition_name=comp.name if comp else "",
        competition_icon=comp.icon if comp else "🏆",
        edition_name=edition.name if edition else "",
        edition_year=edition.year if edition else 0,
    )


# ---------- 公开接口 ----------
@router.get("", response_model=list[CompetitionOut])
def list_competitions(db: Session = Depends(get_db)):
    return db.query(Competition).order_by(Competition.id.desc()).all()


@router.get("/{cid}/editions", response_model=list[CompetitionEditionOut])
def list_editions(
    cid: int,
    current: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    comp = db.query(Competition).filter(Competition.id == cid).first()
    if not comp:
        raise HTTPException(status_code=404, detail="比赛不存在")
    editions = (
        db.query(CompetitionEdition)
        .filter(CompetitionEdition.competition_id == cid)
        .order_by(CompetitionEdition.year.desc())
        .all()
    )
    earned = _edition_points(db, current, [e.id for e in editions])
    return [
        CompetitionEditionOut(
            id=e.id,
            competition_id=e.competition_id,
            name=e.name,
            year=e.year,
            created_at=e.created_at,
            my_points=earned.get(e.id, 0),
        )
        for e in editions
    ]


@router.get("/challenges/{challenge_id}", response_model=CompetitionChallengeDetailOut)
def get_competition_challenge(
    challenge_id: int,
    current: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """比赛题目详情（供题目详情页使用）。"""
    ch = db.get(CompetitionChallenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return _detail(ch, db, current)


@router.get("/challenges/{challenge_id}/attachment")
def download_competition_attachment(challenge_id: int, db: Session = Depends(get_db)):
    ch = db.get(CompetitionChallenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    if not ch.attachment:
        raise HTTPException(status_code=404, detail="该题目没有附件")
    path = os.path.join(UPLOAD_DIR, ch.attachment)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="附件文件不存在")
    return FileResponse(path, filename=ch.attachment)


@router.post("/challenges/{challenge_id}/submit", response_model=SolveOut)
def submit_competition_flag(
    challenge_id: int,
    body: SolveIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """校验比赛题目 flag，并把解题记录持久化。"""
    ch = db.get(CompetitionChallenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    already = (
        db.query(CompetitionSolve)
        .filter(
            CompetitionSolve.user_id == current.id,
            CompetitionSolve.challenge_id == challenge_id,
        )
        .first()
    )
    if already:
        return SolveOut(success=False, message="你已经解出过这道题了", points=0)

    if body.flag.strip() != (ch.flag or "").strip():
        return SolveOut(success=False, message="Flag 不正确，再试试", points=0)

    db.add(CompetitionSolve(user_id=current.id, challenge_id=ch.id, points=ch.points))
    ch.solved_count += 1
    db.commit()
    return SolveOut(success=True, message=f"恭喜！Flag 正确，+{ch.points} 分", points=ch.points)


@router.get("/editions/{eid}/challenges", response_model=list[CompetitionChallengeOut])
def list_edition_challenges(
    eid: int,
    current: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    rows = db.query(CompetitionChallenge).filter(CompetitionChallenge.edition_id == eid).all()
    solved = _solved_ids(db, current, [r.id for r in rows])
    return [
        CompetitionChallengeOut(
            id=r.id,
            edition_id=r.edition_id,
            title=r.title,
            category=r.category,
            difficulty=r.difficulty,
            description=r.description,
            attachment=r.attachment,
            created_at=r.created_at,
            points=r.points,
            solved_count=r.solved_count,
            solved_by_me=r.id in solved,
        )
        for r in rows
    ]


# ---------- 管理员接口 ----------
@admin_router.post("", response_model=CompetitionOut)
def create_competition(
    body: CompetitionIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    comp = Competition(**body.model_dump())
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


@admin_router.post("/editions", response_model=CompetitionEditionOut)
def create_edition(
    body: CompetitionEditionIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    comp = db.query(Competition).filter(Competition.id == body.competition_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="比赛不存在")
    ed = CompetitionEdition(**body.model_dump())
    db.add(ed)
    db.commit()
    db.refresh(ed)
    return ed


@admin_router.post("/challenges", response_model=CompetitionChallengeOut)
def create_competition_challenge(
    body: CompetitionChallengeIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    ed = db.query(CompetitionEdition).filter(CompetitionEdition.id == body.edition_id).first()
    if not ed:
        raise HTTPException(status_code=404, detail="届次不存在")
    ch = CompetitionChallenge(**body.model_dump())
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


class PasswordConfirm(BaseModel):
    password: str


def _check_password(user: User, db: Session, password: str) -> None:
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user or not verify_password(password, db_user.hashed_password):
        raise HTTPException(status_code=403, detail="管理员密码错误")


@admin_router.delete("/{cid}")
def delete_competition(
    cid: int,
    body: PasswordConfirm,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    _check_password(admin, db, body.password)
    comp = db.query(Competition).filter(Competition.id == cid).first()
    if not comp:
        raise HTTPException(status_code=404, detail="比赛不存在")
    # 级联删除届次和题目
    eds = db.query(CompetitionEdition).filter(CompetitionEdition.competition_id == cid).all()
    for ed in eds:
        db.query(CompetitionChallenge).filter(CompetitionChallenge.edition_id == ed.id).delete()
        db.delete(ed)
    db.delete(comp)
    db.commit()
    return {"success": True}


@admin_router.delete("/editions/{eid}")
def delete_edition(
    eid: int,
    body: PasswordConfirm,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    _check_password(admin, db, body.password)
    ed = db.query(CompetitionEdition).filter(CompetitionEdition.id == eid).first()
    if not ed:
        raise HTTPException(status_code=404, detail="届次不存在")
    db.query(CompetitionChallenge).filter(CompetitionChallenge.edition_id == eid).delete()
    db.delete(ed)
    db.commit()
    return {"success": True}


@admin_router.delete("/challenges/{cid}")
def delete_competition_challenge(
    cid: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    ch = db.query(CompetitionChallenge).filter(CompetitionChallenge.id == cid).first()
    if not ch:
        raise HTTPException(status_code=404, detail="题目不存在")
    db.delete(ch)
    db.commit()
    return {"success": True}


@admin_router.patch("/{cid}", response_model=CompetitionOut)
def update_competition(
    cid: int,
    body: CompetitionIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    comp = db.query(Competition).filter(Competition.id == cid).first()
    if not comp:
        raise HTTPException(status_code=404, detail="比赛不存在")
    for k, v in body.model_dump().items():
        setattr(comp, k, v)
    db.commit()
    db.refresh(comp)
    return comp
