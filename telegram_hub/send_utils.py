from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from telegram_hub.clients import pretty_json
from telegram_hub.config import Settings
from telegram_hub.textutil import chunk_text

TG_TEXT_CAP = 4000


async def reply_json(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
    payload: Any,
    caption: str | None = None,
) -> None:
    text = pretty_json(payload)
    soft = max(512, settings.heavy_json_as_file_over_bytes)
    msg = update.effective_message
    if not msg:
        return
    if len(text.encode("utf-8")) <= soft:
        for part in chunk_text(text, TG_TEXT_CAP):
            await msg.reply_text(part)
        return
    name = f"hub_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    bio = io.BytesIO(text.encode("utf-8"))
    bio.name = name
    await msg.reply_document(document=bio, caption=caption or "Відповідь API (великий JSON)")


async def reply_text_safe(update: Update, text: str) -> None:
    msg = update.effective_message
    if not msg:
        return
    for part in chunk_text(text, TG_TEXT_CAP):
        await msg.reply_text(part)


async def reply_bytes_document(
    update: Update,
    data: bytes,
    filename: str,
    caption: str | None = None,
) -> None:
    msg = update.effective_message
    if not msg:
        return
    bio = io.BytesIO(data)
    bio.name = filename
    await msg.reply_document(document=bio, caption=caption)
