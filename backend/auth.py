import hashlib
import hmac
import json
import os
from urllib.parse import unquote
from fastapi import HTTPException, Header
from typing import Optional


ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "810376283"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


def verify_telegram_webapp(init_data: str) -> dict:
    """Verify Telegram Mini App initData and return user info."""
    parsed = {}
    for part in init_data.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            parsed[k] = unquote(v)

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="No hash in init_data")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid init_data signature")

    user_data = json.loads(parsed.get("user", "{}"))
    return user_data


def get_current_user(x_telegram_init_data: Optional[str] = Header(None)) -> dict:
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram auth header")
    return verify_telegram_webapp(x_telegram_init_data)


def require_admin(x_telegram_init_data: Optional[str] = Header(None)) -> dict:
    user = get_current_user(x_telegram_init_data)
    if user.get("id") != ADMIN_TELEGRAM_ID:
        raise HTTPException(status_code=403, detail="Admin only")
    return user
