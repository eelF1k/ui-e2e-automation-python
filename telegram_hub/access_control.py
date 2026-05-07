from __future__ import annotations

import time
from collections import deque

from telegram import Update
from telegram.ext import ContextTypes

from telegram_hub.config import Settings


def allowed_user_ids(settings: Settings) -> set[int]:
    raw = (settings.telegram_allowed_user_ids or "").strip()
    if not raw:
        return set()
    ids: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if part.isdigit():
            ids.add(int(part))
    return ids


def admin_chat_ids(settings: Settings) -> set[int]:
    raw = (settings.telegram_admin_chat_ids or "").strip()
    if not raw:
        return set()
    ids: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


async def guard_request(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: Settings) -> bool:
    if not await ensure_access(update, settings):
        return False
    uid = update.effective_user.id if update.effective_user else None
    if not rate_limit_ok(uid, context, settings):
        if update.effective_message:
            await update.effective_message.reply_text("Забагато запитів. Спробуйте за хвилину.")
        if update.callback_query:
            await update.callback_query.answer("Rate limit", show_alert=True)
        return False
    return True


async def ensure_access(update: Update, settings: Settings) -> bool:
    allowed = allowed_user_ids(settings)
    if not allowed:
        return True
    uid = update.effective_user.id if update.effective_user else None
    if uid is None or uid not in allowed:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Доступ заборонено. Додайте свій Telegram user id у TELEGRAM_ALLOWED_USER_IDS або /whoami."
            )
        if update.callback_query and update.callback_query.message:
            await update.callback_query.answer("Немає доступу", show_alert=True)
        return False
    return True


def rate_limit_ok(user_id: int | None, context: ContextTypes.DEFAULT_TYPE, settings: Settings) -> bool:
    if user_id is None:
        return True
    limit = max(1, settings.rate_limit_per_minute)
    bucket: dict[int, deque[float]] = context.application.bot_data.setdefault("_rl", {})
    now = time.monotonic()
    q = bucket.setdefault(user_id, deque())
    while q and now - q[0] > 60.0:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True
