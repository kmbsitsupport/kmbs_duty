from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models import Checklist, ChecklistItem, Person, TelegramUser
from auth import get_current_user, require_admin

router = APIRouter(prefix="/checklists", tags=["checklists"])


class ChecklistItemCreate(BaseModel):
    text: str
    order: int = 0


class ChecklistCreate(BaseModel):
    title: str
    person_id: Optional[int] = None
    items: List[ChecklistItemCreate] = []


class ItemToggle(BaseModel):
    is_done: bool


@router.post("")
async def create_checklist(
    data: ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    checklist = Checklist(
        title=data.title,
        person_id=data.person_id,
        created_by_id=admin.get("id"),
    )
    db.add(checklist)
    await db.flush()

    for i, item in enumerate(data.items):
        db.add(ChecklistItem(
            checklist_id=checklist.id,
            text=item.text,
            order=item.order or i,
        ))

    await db.commit()
    return {"id": checklist.id, "message": "Чеклист створено"}


@router.get("/my")
async def get_my_checklists(
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
        select(Checklist).where(Checklist.person_id == person.id)
    )
    checklists = result3.scalars().all()

    out = []
    for cl in checklists:
        items_result = await db.execute(
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == cl.id)
            .order_by(ChecklistItem.order)
        )
        items = items_result.scalars().all()
        out.append({
            "id": cl.id,
            "title": cl.title,
            "is_completed": cl.is_completed,
            "created_at": cl.created_at.isoformat(),
            "items": [
                {"id": it.id, "text": it.text, "is_done": it.is_done, "order": it.order}
                for it in items
            ],
        })

    return out


@router.patch("/items/{item_id}")
async def toggle_item(
    item_id: int,
    data: ItemToggle,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(ChecklistItem).where(ChecklistItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")

    item.is_done = data.is_done
    await db.commit()
    return {"message": "Оновлено"}


@router.get("")
async def get_all_checklists(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Checklist))
    checklists = result.scalars().all()
    out = []
    for cl in checklists:
        items_result = await db.execute(
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == cl.id)
            .order_by(ChecklistItem.order)
        )
        items = items_result.scalars().all()
        out.append({
            "id": cl.id,
            "title": cl.title,
            "person_id": cl.person_id,
            "is_completed": cl.is_completed,
            "items": [{"id": i.id, "text": i.text, "is_done": i.is_done} for i in items],
        })
    return out


@router.delete("/{checklist_id}")
async def delete_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Checklist).where(Checklist.id == checklist_id))
    cl = result.scalar_one_or_none()
    if not cl:
        raise HTTPException(404, "Not found")
    await db.delete(cl)
    await db.commit()
    return {"message": "Видалено"}
