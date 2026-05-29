import os
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db
from models import TelegramUser
from auth import require_admin

router = APIRouter(prefix="/notifications", tags=["notifications"])

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5173")


class BroadcastRequest(BaseModel):
    message: str


@router.post("/broadcast")
async def broadcast(
    data: BroadcastRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(TelegramUser))
    users = result.scalars().all()

    sent = 0
    admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "810376283"))

    async with httpx.AsyncClient() as client:
        for user in users:
            if user.telegram_id == admin_id:
                continue
            try:
                await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": user.telegram_id,
                        "text": data.message,
                        "reply_markup": {
                            "inline_keyboard": [[
                                {
                                    "text": "📋 Відкрити застосунок",
                                    "web_app": {"url": f"{WEBAPP_URL}/app"},
                                }
                            ]]
                        },
                    },
                )
                sent += 1
            except Exception:
                pass

    return {"sent": sent}
