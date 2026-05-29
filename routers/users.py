from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import TelegramUser

router = APIRouter(prefix="/users", tags=["users"])


class UserRegister(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_admin: bool = False


@router.post("/register")
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == data.telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = TelegramUser(
            telegram_id=data.telegram_id,
            username=data.username,
            first_name=data.first_name,
            is_admin=data.is_admin,
        )
        db.add(user)
    else:
        if data.username:
            user.username = data.username
        if data.first_name:
            user.first_name = data.first_name

    await db.commit()
    return {"id": user.id, "telegram_id": user.telegram_id}


@router.get("/all")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TelegramUser))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "first_name": u.first_name,
            "is_admin": u.is_admin,
        }
        for u in users
    ]
