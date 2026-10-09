"""用户相关路由。"""
from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..models import User
from ..schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current: User = Depends(get_current_user)):
    return current
