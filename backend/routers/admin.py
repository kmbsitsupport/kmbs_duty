import os
import io
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional
from pydantic import BaseModel

from database import get_db
from models import Person, ScheduleEntry, TelegramUser
from auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


class PersonAssign(BaseModel):
    person_id: int
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None


class NewAdminAssign(BaseModel):
    telegram_user_id: int


@router.post("/upload-schedule")
async def upload_schedule(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    content = await file.read()
    filename = file.filename or "schedule.xlsx"

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))

    df.columns = [str(c).strip().lower() for c in df.columns]

    entries_added = 0
    persons_created = set()

    for _, row in df.iterrows():
        raw_name = str(row.get("name", row.get("імʼя", row.get("ім'я", row.get("фіо", ""))))).strip()
        date = str(row.get("date", row.get("дата", ""))).strip()
        time_start = str(row.get("time_start", row.get("початок", row.get("час", "")))).strip()
        time_end = str(row.get("time_end", row.get("кінець", ""))).strip()
        description = str(row.get("description", row.get("опис", row.get("завдання", "")))).strip()
        location = str(row.get("location", row.get("місце", ""))).strip()

        if not raw_name or raw_name == "nan":
            continue

        if raw_name not in persons_created:
            existing = await db.execute(select(Person).where(Person.name == raw_name))
            person = existing.scalar_one_or_none()
            if not person:
                person = Person(name=raw_name)
                db.add(person)
                await db.flush()
            persons_created.add(raw_name)

        entry = ScheduleEntry(
            raw_name=raw_name,
            date=date if date != "nan" else "",
            time_start=time_start if time_start != "nan" else "",
            time_end=time_end if time_end != "nan" else "",
            description=description if description != "nan" else "",
            location=location if location != "nan" else "",
            source_file=filename,
        )
        db.add(entry)
        entries_added += 1

    await db.commit()

    persons_result = await db.execute(select(Person))
    all_persons = persons_result.scalars().all()

    return {
        "message": f"Завантажено {entries_added} записів",
        "persons": [{"id": p.id, "name": p.name} for p in all_persons],
    }


@router.get("/persons")
async def get_persons(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(Person))
    persons = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "telegram_user_id": p.telegram_user_id,
            "telegram_username": p.telegram_username,
        }
        for p in persons
    ]


@router.post("/assign-person")
async def assign_person(
    data: PersonAssign,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Person).where(Person.id == data.person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(404, "Person not found")

    if data.telegram_user_id:
        result2 = await db.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == data.telegram_user_id)
        )
        tg_user = result2.scalar_one_or_none()
        if not tg_user:
            tg_user = TelegramUser(telegram_id=data.telegram_user_id)
            db.add(tg_user)
            await db.flush()
        person.telegram_user_id = tg_user.id

    if data.telegram_username:
        person.telegram_username = data.telegram_username

    await db.commit()
    return {"message": "Призначено успішно"}


@router.post("/assign-admin")
async def assign_admin(
    data: NewAdminAssign,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == data.telegram_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = TelegramUser(telegram_id=data.telegram_user_id, is_admin=True)
        db.add(user)
    else:
        user.is_admin = True
    await db.commit()
    return {"message": f"Користувач {data.telegram_user_id} тепер адмін"}


@router.get("/schedule")
async def get_schedule(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(ScheduleEntry))
    entries = result.scalars().all()
    return [
        {
            "id": e.id,
            "raw_name": e.raw_name,
            "date": e.date,
            "time_start": e.time_start,
            "time_end": e.time_end,
            "description": e.description,
            "location": e.location,
            "person_id": e.person_id,
        }
        for e in entries
    ]
