from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import Alert, Person
from auth import require_admin

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    person_id: int
    message: str
    send_at: Optional[str] = None
    repeat_daily: bool = False


@router.post("")
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Person).where(Person.id == data.person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(404, "Person not found")

    send_at = None
    if data.send_at:
        try:
            send_at = datetime.fromisoformat(data.send_at)
        except ValueError:
            raise HTTPException(400, "Invalid date format, use ISO 8601")

    alert = Alert(
        person_id=data.person_id,
        message=data.message,
        send_at=send_at,
        repeat_daily=data.repeat_daily,
    )
    db.add(alert)
    await db.commit()
    return {"id": alert.id, "message": "Алерт створено"}


@router.get("")
async def get_alerts(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(Alert))
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "person_id": a.person_id,
            "message": a.message,
            "send_at": a.send_at.isoformat() if a.send_at else None,
            "is_sent": a.is_sent,
            "is_active": a.is_active,
            "repeat_daily": a.repeat_daily,
        }
        for a in alerts
    ]


@router.get("/pending")
async def get_pending_alerts(db: AsyncSession = Depends(get_db)):
    """Internal endpoint for bot to fetch pending alerts."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Alert).where(Alert.is_active == True, Alert.is_sent == False)
    )
    alerts = result.scalars().all()

    pending = []
    for a in alerts:
        if a.send_at is None or a.send_at <= now:
            result2 = await db.execute(select(Person).where(Person.id == a.person_id))
            person = result2.scalar_one_or_none()
            if person:
                pending.append({
                    "id": a.id,
                    "message": a.message,
                    "telegram_user_id": person.telegram_user_id,
                    "telegram_username": person.telegram_username,
                    "repeat_daily": a.repeat_daily,
                })

    return pending


@router.post("/{alert_id}/mark-sent")
async def mark_sent(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Internal endpoint for bot to mark alert as sent."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Not found")

    if alert.repeat_daily:
        from datetime import timedelta
        alert.send_at = (alert.send_at or datetime.utcnow()) + timedelta(days=1)
    else:
        alert.is_sent = True

    await db.commit()
    return {"message": "OK"}


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Not found")
    await db.delete(alert)
    await db.commit()
    return {"message": "Видалено"}
