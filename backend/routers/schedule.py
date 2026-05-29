from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import ScheduleEntry, Person, TelegramUser
from auth import get_current_user

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/my")
async def get_my_schedule(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    tg_id = user.get("id")

    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == tg_id)
    )
    tg_user = result.scalar_one_or_none()
    if not tg_user:
        return []

    result2 = await db.execute(
        select(Person).where(Person.telegram_user_id == tg_user.id)
    )
    person = result2.scalar_one_or_none()
    if not person:
        return []

    result3 = await db.execute(
        select(ScheduleEntry)
        .where(ScheduleEntry.person_id == person.id)
        .order_by(ScheduleEntry.date, ScheduleEntry.time_start)
    )
    entries = result3.scalars().all()

    return [
        {
            "id": e.id,
            "date": e.date,
            "time_start": e.time_start,
            "time_end": e.time_end,
            "description": e.description,
            "location": e.location,
        }
        for e in entries
    ]
