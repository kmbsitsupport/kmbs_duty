import os
import logging
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5173")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "810376283"))


async def send_pending_alerts(bot: Bot):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/alerts/pending")
            if resp.status_code != 200:
                return
            alerts = resp.json()

        for alert in alerts:
            tg_user_id = alert.get("telegram_user_id")
            if not tg_user_id:
                continue

            from sqlalchemy import select
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📋 Відкрити застосунок",
                    web_app=WebAppInfo(url=f"{WEBAPP_URL}/app"),
                )],
            ])

            try:
                await bot.send_message(
                    chat_id=tg_user_id,
                    text=f"🔔 {alert['message']}",
                    reply_markup=kb,
                )
                async with httpx.AsyncClient() as client:
                    await client.post(f"{BACKEND_URL}/alerts/{alert['id']}/mark-sent")
            except Exception as e:
                logger.error(f"Failed to send alert {alert['id']}: {e}")

    except Exception as e:
        logger.error(f"Scheduler error: {e}")


async def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_pending_alerts,
        "interval",
        minutes=1,
        args=[bot],
        id="send_alerts",
    )
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler
