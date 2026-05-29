import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

router = Router()

ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "810376283"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5173")


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_TELEGRAM_ID


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message):
        await message.answer("⛔ Немає доступу.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⚙️ Відкрити адмінку",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"),
        )],
    ])
    await message.answer("Відкрий адмін-панель:", reply_markup=kb)


@router.message(Command("notify"))
async def cmd_notify(message: Message):
    """Send notification to all users with their app link."""
    if not is_admin(message):
        await message.answer("⛔ Немає доступу.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Використання: /notify <текст повідомлення>")
        return

    text = args[1]
    import httpx
    from handlers.start import BACKEND_URL

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/users/all")
        users = resp.json()

    bot = message.bot
    sent = 0
    for user in users:
        if user.get("telegram_id") and user["telegram_id"] != ADMIN_TELEGRAM_ID:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📋 Відкрити застосунок",
                    web_app=WebAppInfo(url=f"{WEBAPP_URL}/app"),
                )],
            ])
            try:
                await bot.send_message(user["telegram_id"], text, reply_markup=kb)
                sent += 1
            except Exception:
                pass

    await message.answer(f"✅ Надіслано {sent} користувачам.")
