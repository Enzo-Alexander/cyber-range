"""题目 / 排行榜 / 管理接口。"""
import os
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, get_current_user_optional, require_role
from ..models import Challenge, Favorite, Notification, SolveRecord, User
from ..schemas import (
    AdminChallengeOut,
    ChallengeCard,
    ChallengeIn,
    ChallengeOut,
    ChallengeSubmitIn,
    ChallengeUpdate,
    LeaderboardEntry,
    SolverOut,
    SolveIn,
    SolveOut,
)

router = APIRouter(prefix="/challenges", tags=["challenges"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

CATEGORIES = ["逆向工程", "二进制漏洞", "密码学", "Web安全", "流量分析", "数字取证"]

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _card(ch: Challenge, solved_ids: set[int]) -> ChallengeCard:
    return ChallengeCard(
        id=ch.id,
        title=ch.title,
        category=ch.category,
        difficulty=ch.difficulty,
        points=ch.points,
        status=ch.status,
        solved_count=ch.solved_count,
        solved_by_me=ch.id in solved_ids,
    )


def _notify_admins(db: Session, submitter: User, challenge: Challenge) -> None:
    admins = (
        db.query(User)
        .filter(User.role == "admin", User.is_active.is_(True))
        .all()
    )
    for admin in admins:
        db.add(
            Notification(
                user_id=admin.id,
                type="challenge_submitted",
                title="新的题目待审核",
                content=f"{submitter.username} 提交了题目《{challenge.title}》，请前往题目审核。",
                related_challenge_id=challenge.id,
            )
        )


def _notify_submitter(db: Session, challenge: Challenge, approved: bool) -> None:
    submitter = db.query(User).filter(User.username == challenge.author).first()
    if submitter is None or submitter.role == "admin":
        return
    if approved:
        title = "题目审核通过"
        content = f"你提交的题目《{challenge.title}》已通过审核并上架。"
        notice_type = "challenge_approved"
    else:
        title = "题目审核未通过"
        content = f"你提交的题目《{challenge.title}》未通过审核。"
        notice_type = "challenge_rejected"
    db.add(
        Notification(
            user_id=submitter.id,
            type=notice_type,
            title=title,
            content=content,
            related_challenge_id=challenge.id,
        )
    )


@router.get("/", response_model=list[ChallengeCard])
def list_challenges(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    q = db.query(Challenge).filter(Challenge.status == "published")
    if category and category != "全部":
        q = q.filter(Challenge.category == category)
    if search:
        q = q.filter(Challenge.title.ilike(f"%{search}%"))
    challenges = q.order_by(Challenge.points.desc()).all()

    solved_ids: set[int] = set()
    if current is not None:
        solved_ids = {
            r.challenge_id
            for r in db.query(SolveRecord).filter(SolveRecord.user_id == current.id).all()
        }
    return [_card(c, solved_ids) for c in challenges]


@router.get("/categories")
def list_categories():
    return CATEGORIES


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(
            SolveRecord.user_id,
            func.sum(SolveRecord.points).label("total"),
            func.count(SolveRecord.id).label("cnt"),
            func.max(SolveRecord.solved_at).label("last"),
        )
        .group_by(SolveRecord.user_id)
        .order_by(func.sum(SolveRecord.points).desc(), func.max(SolveRecord.solved_at).asc())
        .all()
    )
    users = {u.id: u for u in db.query(User).all()}
    result: list[LeaderboardEntry] = []
    for i, (uid, total, cnt, last) in enumerate(rows, start=1):
        u = users.get(uid)
        if not u:
            continue
        result.append(
            LeaderboardEntry(
                rank=i,
                username=u.username,
                total_points=int(total),
                solved_count=int(cnt),
                last_solved_at=last,
            )
        )
    return result


@router.post("/submit", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED)
def submit_challenge(
    body: ChallengeSubmitIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """普通用户提交题目，统一进入待审核状态。"""
    if body.category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="题目分类无效")
    ch = Challenge(
        title=body.title,
        category=body.category,
        difficulty=body.difficulty,
        points=body.points,
        description=body.description,
        attachment=body.attachment,
        flag=body.flag,
        author=current.username,
        status="pending",
    )
    db.add(ch)
    db.flush()
    _notify_admins(db, current, ch)
    db.commit()
    db.refresh(ch)
    return ch


@router.post("/attachments")
def upload_submission_attachment(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    name = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"filename": name, "original": file.filename}


@router.get("/{challenge_id}", response_model=ChallengeOut)
def get_challenge(
    challenge_id: int,
    current: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    ch = db.get(Challenge, challenge_id)
    if ch is None or ch.status != "published":
        raise HTTPException(status_code=404, detail="题目不存在或未上架")
    favorited = bool(
        current
        and db.query(Favorite.id)
        .filter(Favorite.user_id == current.id, Favorite.challenge_id == ch.id)
        .first()
    )
    return ChallengeOut.model_validate(ch).model_copy(
        update={"favorited_by_me": favorited}
    )


@router.get("/{challenge_id}/attachment")
def download_attachment(challenge_id: int, db: Session = Depends(get_db)):
    ch = db.get(Challenge, challenge_id)
    if ch is None or ch.status != "published":
        raise HTTPException(status_code=404, detail="题目不存在或未上架")
    if not ch.attachment:
        raise HTTPException(status_code=404, detail="该题目没有附件")
    path = os.path.join(UPLOAD_DIR, ch.attachment)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="附件文件不存在")
    return FileResponse(path, filename=ch.attachment)


@router.get("/{challenge_id}/solvers", response_model=list[SolverOut])
def challenge_solvers(challenge_id: int, db: Session = Depends(get_db)):
    if db.get(Challenge, challenge_id) is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    rows = (
        db.query(SolveRecord, User)
        .join(User, User.id == SolveRecord.user_id)
        .filter(SolveRecord.challenge_id == challenge_id)
        .order_by(SolveRecord.solved_at.desc())
        .limit(8)
        .all()
    )
    return [SolverOut(username=u.username, solved_at=r.solved_at) for r, u in rows]


@router.get("/{challenge_id}/related", response_model=list[ChallengeCard])
def related_challenges(challenge_id: int, db: Session = Depends(get_db)):
    ch = db.get(Challenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    others = (
        db.query(Challenge)
        .filter(Challenge.category == ch.category, Challenge.id != ch.id, Challenge.status == "published")
        .order_by(Challenge.points.desc())
        .limit(5)
        .all()
    )
    return [_card(c, set()) for c in others]


@router.post("/{challenge_id}/submit", response_model=SolveOut)
def submit_flag(
    challenge_id: int,
    body: SolveIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = db.get(Challenge, challenge_id)
    if ch is None or ch.status != "published":
        raise HTTPException(status_code=404, detail="题目不存在或未上架")

    already = (
        db.query(SolveRecord)
        .filter(SolveRecord.challenge_id == challenge_id, SolveRecord.user_id == current.id)
        .first()
    )
    if already:
        return SolveOut(success=False, message="你已经解出过这道题了", points=0)

    if body.flag.strip() != ch.flag.strip():
        return SolveOut(success=False, message="Flag 不正确，再试试", points=0)

    rec = SolveRecord(user_id=current.id, challenge_id=ch.id, points=ch.points)
    db.add(rec)
    ch.solved_count += 1
    db.commit()
    return SolveOut(success=True, message="恭喜！Flag 正确，得分已入账", points=ch.points)


# ---------- 管理员 ----------
@admin_router.get("/challenges", response_model=list[AdminChallengeOut])
def admin_list_challenges(
    challenge_status: Literal["published", "pending", "draft", "rejected"] | None = Query(
        default=None, alias="status"
    ),
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Challenge)
    if challenge_status:
        query = query.filter(Challenge.status == challenge_status)
    return query.order_by(Challenge.created_at.desc()).all()


@admin_router.get("/challenges/{challenge_id}/attachment")
def admin_download_attachment(
    challenge_id: int,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ch = db.get(Challenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    if not ch.attachment:
        raise HTTPException(status_code=404, detail="该题目没有附件")
    path = os.path.join(UPLOAD_DIR, ch.attachment)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="附件文件不存在")
    return FileResponse(path, filename=ch.attachment)


@admin_router.get("/stats")
def admin_stats(
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    total = db.query(Challenge).count()
    pending = db.query(Challenge).filter(Challenge.status == "pending").count()
    today = db.query(Challenge).filter(
        func.date(Challenge.created_at) == func.date("now")
    ).count()
    users = db.query(User).count()
    return {"challenge_total": total, "pending": pending, "today": today, "user_total": users}


@admin_router.post("/challenges", response_model=AdminChallengeOut, status_code=status.HTTP_201_CREATED)
def admin_create_challenge(
    body: ChallengeIn,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ch = Challenge(
        title=body.title,
        category=body.category,
        difficulty=body.difficulty,
        points=body.points,
        description=body.description,
        attachment=body.attachment,
        flag=body.flag,
        author=admin.username,
        status=body.status,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


@admin_router.put("/challenges/{challenge_id}", response_model=AdminChallengeOut)
def admin_update_challenge(
    challenge_id: int,
    body: ChallengeUpdate,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ch = db.get(Challenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    previous_status = ch.status
    for field in ("title", "category", "difficulty", "points", "description", "attachment", "flag", "status"):
        value = getattr(body, field)
        if value is not None:
            setattr(ch, field, value)
    if previous_status != ch.status and ch.status in ("published", "rejected"):
        _notify_submitter(db, ch, approved=ch.status == "published")
    if previous_status == "pending" and ch.status != "pending":
        (
            db.query(Notification)
            .filter(
                Notification.user_id == admin.id,
                Notification.type == "challenge_submitted",
                Notification.related_challenge_id == ch.id,
            )
            .update({Notification.is_read: True}, synchronize_session=False)
        )
    db.commit()
    db.refresh(ch)
    return ch


@admin_router.delete("/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_challenge(
    challenge_id: int,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ch = db.get(Challenge, challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    db.delete(ch)
    db.commit()


@admin_router.post("/attachments")
def admin_upload_attachment(
    file: UploadFile = File(...),
    admin: User = Depends(require_role("admin")),
):
    """上传题目附件，返回存储文件名（用于写入题目 attachment 字段）。"""
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    name = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"filename": name, "original": file.filename}
