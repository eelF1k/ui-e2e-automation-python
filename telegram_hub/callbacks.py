from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from telegram_hub.access_control import guard_request
from telegram_hub.clients import BackendHub
from telegram_hub.config import Settings
from telegram_hub.keyboards import kb_main, kb_p2, kb_p3, kb_p4, kb_p5
from telegram_hub.send_utils import reply_bytes_document, reply_json

logger = logging.getLogger(__name__)


async def on_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    hub: BackendHub = context.bot_data["hub"]
    data = query.data
    chat = query.message.chat

    async def edit(text: str, markup):
        try:
            await query.edit_message_text(text, reply_markup=markup)
        except BadRequest:
            await chat.send_message(text, reply_markup=markup)

    if data == "m|hm":
        await edit("Головне меню — оберіть проєкт або дію.", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
        return
    if data == "m|p4":
        await edit("Project4 — RAG / ingestion / ops.", kb_p4())
        return
    if data == "m|p5":
        await edit("Project5 — Retail copilot (analytics, NL-SQL, LLM).", kb_p5())
        return
    if data == "m|p3":
        await edit("Project3 — Banking Ops каркас API.", kb_p3())
        return
    if data == "m|p2":
        await edit("Project2 — Mini SaaS (Django JWT + інвойси).", kb_p2())
        return

    if data == "a|wiz":
        await chat.send_message("Запуск: команду /ingest_wizard або /wiz")
        await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
        return

    if data == "a|help":
        await chat.send_message("Командний список: /help або /cmds")
        await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
        return

    if data == "a|stat":
        lines = await _collect_status(settings, hub)
        await chat.send_message("\n".join(lines))
        await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
        return

    if data.startswith("3|"):
        base = settings.project3_api_base
        if not base:
            await chat.send_message("Немає PROJECT3_API_BASE у .env")
            await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
            return
        try:
            if data == "3|hl":
                body = await hub.project3_health(base)
                await reply_json(update, context, settings, body, caption="P3 health")
            elif data == "3|rt":
                body = await hub.project3_root(base)
                await reply_json(update, context, settings, body, caption="P3 /")
        except Exception as exc:
            await chat.send_message(f"P3: {exc!s}")
        await edit("Project3:", kb_p3())
        return

    if data.startswith("2|"):
        base = settings.project2_api_base
        if not base:
            await chat.send_message("Немає PROJECT2_API_BASE")
            await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
            return
        try:
            if data == "2|rt":
                body = await hub.http_get_json(base.rstrip("/") + "/")
                await reply_json(update, context, settings, body, caption="P2 root")
            elif data == "2|in":
                if not settings.project2_jwt:
                    await chat.send_message("Потрібен PROJECT2_JWT")
                else:
                    body = await hub.project2_list_invoices(base, settings.project2_jwt)
                    await reply_json(update, context, settings, body, caption="P2 invoices")
        except Exception as exc:
            await chat.send_message(f"P2: {exc!s}")
        await edit("Project2:", kb_p2())
        return

    if data.startswith("4|"):
        base = settings.project4_api_base
        if not base:
            await chat.send_message("Немає PROJECT4_API_BASE")
            await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
            return
        try:
            if data == "4|hl":
                await reply_json(update, context, settings, await hub.project4_health(base), caption="P4 health")
            elif data == "4|rd":
                await reply_json(update, context, settings, await hub.project4_ready(base), caption="P4 ready")
            elif data == "4|mt":
                plain, ctype = await hub.project4_metrics_plain(base)
                await reply_bytes_document(
                    update,
                    plain.encode("utf-8", errors="replace"),
                    "p4_metrics.txt",
                    caption=f"P4 metrics ({ctype})",
                )
            elif data == "4|jb":
                await reply_json(update, context, settings, await hub.project4_ops_jobs(base, 15), caption="P4 jobs")
            elif data == "4|au":
                await reply_json(update, context, settings, await hub.project4_ops_audit(base, 20), caption="P4 audit")
        except Exception as exc:
            await chat.send_message(f"P4: {exc!s}")
        await edit("Project4:", kb_p4())
        return

    if data.startswith("5|"):
        base = settings.project5_api_base
        if not base:
            await chat.send_message("Немає PROJECT5_API_BASE")
            await edit("Головне меню:", kb_main(web_app_url=(settings.telegram_web_app_url or "").strip()))
            return
        try:
            if data == "5|hl":
                await reply_json(update, context, settings, await hub.project5_health(base), caption="P5 health")
            elif data == "5|mt":
                plain, ctype = await hub.project5_metrics_plain(base)
                await reply_bytes_document(
                    update,
                    plain.encode("utf-8", errors="replace"),
                    "p5_metrics.txt",
                    caption=f"P5 metrics ({ctype})",
                )
            elif data == "5|rv7":
                await reply_json(update, context, settings, await hub.project5_revenue(base, days=7), caption="P5 revenue")
            elif data == "5|sk7":
                await reply_json(update, context, settings, await hub.project5_top_skus(base, days=7, limit=15), caption="P5 SKU")
        except Exception as exc:
            await chat.send_message(f"P5: {exc!s}")
        await edit("Project5:", kb_p5())
        return


async def _collect_status(settings: Settings, hub: BackendHub) -> list[str]:
    lines: list[str] = ["Статус (watchdog):"]

    async def probe(name: str, coro):
        try:
            data = await coro
            return f"✅ {name}: {data}"
        except Exception as exc:
            return f"❌ {name}: {exc!s}"

    jobs: list = []
    if settings.project3_api_base:
        jobs.append(probe("P3 health", hub.project3_health(settings.project3_api_base)))
    if settings.project4_api_base:
        jobs.append(probe("P4 health", hub.project4_health(settings.project4_api_base)))
        jobs.append(probe("P4 ready", hub.project4_ready(settings.project4_api_base)))
    if settings.project5_api_base:
        jobs.append(probe("P5 health", hub.project5_health(settings.project5_api_base)))
    if not jobs:
        return ["Не задано жодного PROJECT*_API_BASE для перевірки."]
    results = await asyncio.gather(*jobs)
    lines.extend(results)
    return lines
