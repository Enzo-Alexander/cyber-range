"""站内通知接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Notification, User
from ..schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="通知不存在")
    item.is_read = True
    db.commit()
    return {"success": True}


@router.post("/read-all")
def mark_all_notifications_read(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    (
        db.query(Notification)
        .filter(Notification.user_id == current.id, Notification.is_read.is_(False))
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return {"success": True}
