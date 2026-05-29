import os
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import httpx

router = Router()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5173")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "810376283"))


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{BACKEND_URL}/users/register", json={
                "telegram_id": user_id,
                "username": username,
                "first_name": first_name,
                "is_admin": user_id == ADMIN_TELEGRAM_ID,
            })
        except Exception:
            pass

    if user_id == ADMIN_TELEGRAM_ID:
        admin_url = f"{WEBAPP_URL}/admin"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⚙️ Адмін-панель",
                web_app=WebAppInfo(url=admin_url),
            )],
            [InlineKeyboardButton(
                text="📋 Мій розклад",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/app"),
            )],
        ])
        await message.answer(
            f"Привіт, {first_name}! 👋\n\n"
            "У вас є доступ до <b>адмін-панелі</b>.\n"
            "Там можна завантажувати розклади, налаштовувати алерти та чеклісти.",
            reply_markup=kb,
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📋 Відкрити мій розклад",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/app"),
            )],
        ])
        await message.answer(
            f"Привіт, {first_name}! 👋\n\n"
            "Тут ти знайдеш свій розклад та чеклісти.",
            reply_markup=kb,
        )
