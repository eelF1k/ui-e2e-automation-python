from __future__ import annotations

import json
import logging
import re
import shlex
import threading
from datetime import datetime, timezone

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from telegram_hub.bootstrap import post_init as bootstrap_post_init
from telegram_hub.access_control import admin_chat_ids, guard_request
from telegram_hub.callbacks import _collect_status, on_menu_callback
from telegram_hub.clients import BackendHub, pretty_json
from telegram_hub.config import Settings, get_settings
from telegram_hub.keyboards import (
    LBL_HELP,
    LBL_HIDE,
    LBL_INLINE,
    LBL_P4,
    LBL_P5,
    LBL_PANEL,
    LBL_STATUS,
    LBL_WIZ,
    REPLY_NAV_LABELS,
    kb_main,
    kb_p4,
    kb_p5,
    kb_reply,
)
from telegram_hub.send_utils import reply_bytes_document, reply_json, reply_text_safe
from telegram_hub.textutil import chunk_text

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("telegram_hub")

TG_MAX = 4000


class ReplyNavButtonsFilter(filters.MessageFilter):
    def filter(self, message):  # type: ignore[override]
        if not message or not message.text or message.text.startswith("/"):
            return False
        return message.text.strip() in REPLY_NAV_LABELS


class WebAppPayloadFilter(filters.MessageFilter):
    def filter(self, message):  # type: ignore[override]
        return bool(message and getattr(message, "web_app_data", None) is not None)


reply_nav_filter = ReplyNavButtonsFilter()
web_app_payload_filter = WebAppPayloadFilter()

(W_SRC, W_TXT) = range(2)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    wa = (settings.telegram_web_app_url or "").strip()
    intro = (
        "petlab-telegram-gateway · важкий локальний хаб (Project1–5).\n\n"
        "Знизу — reply-панель + (якщо задано HTTPS) Mini App.\n"
        "Inline-шари в наступному повідомленні.\n\n"
        "Налаштуйте `.env`: TELEGRAM_WEB_APP_URL (публічний HTTPS через тунель до веб-сервера)."
    )
    await update.message.reply_text(intro, reply_markup=kb_reply(web_app_url=wa))
    await update.message.reply_text("Inline-меню проєктів:", reply_markup=kb_main(web_app_url=wa))


async def cmd_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    wa = (settings.telegram_web_app_url or "").strip()
    await update.message.reply_text("Reply-клавіатура увімкнена.", reply_markup=kb_reply(web_app_url=wa))


async def cmd_hide_kb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    await update.message.reply_text("Клавіатуру прибрано.", reply_markup=ReplyKeyboardRemove())


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    url = (settings.telegram_web_app_url or "").strip()
    if not url:
        await update.message.reply_text(
            "Міні-додаток не налаштований.\n"
            "1) `python -m telegram_hub.webapp_server` (порт 8787)\n"
            "2) Прокиньте HTTPS (Cloudflare Tunnel / ngrok).\n"
            "3) TELEGRAM_WEB_APP_URL=https://ваш-тунель/ у `.env` і перезапустіть бота."
        )
        return
    await update.message.reply_text(f"Панель (відкрий у чаті або кнопкою меню ▼):\n{url}")


async def route_reply_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if context.user_data.get("in_wiz"):
        await update.message.reply_text("Активний майстер /wiz — спочатку /cancel.")
        return
    label = (update.message.text or "").strip()
    wa = (settings.telegram_web_app_url or "").strip()

    if label == LBL_STATUS:
        await cmd_status(update, context)
    elif label == LBL_HELP:
        await cmd_help(update, context)
    elif label == LBL_INLINE:
        await update.message.reply_text("Оберіть блок:", reply_markup=kb_main(web_app_url=wa))
    elif label == LBL_P4:
        await update.message.reply_text("P4 — оберіть дію:", reply_markup=kb_p4())
    elif label == LBL_P5:
        await update.message.reply_text("P5 — оберіть дію:", reply_markup=kb_p5())
    elif label == LBL_WIZ:
        await update.message.reply_text("Майстер ingest: наберіть у чаті команду /wiz (кнопки під час діалогу вимкніть через /cancel).")
    elif label == LBL_PANEL:
        await cmd_panel(update, context)
    elif label == LBL_HIDE:
        await cmd_hide_kb(update, context)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    text = (
        "Основні:\n/start /cmds /help /whoami /status /dochelp /keyboard /hide_kb /panel\n\n"
        "Інтерфейс: reply-кнопки знизу, inline-меню з /start; Mini App з меню ▼ (якщо TELEGRAM_WEB_APP_URL).\n\n"
        "━━ P1 UI E2E ━━\n/e2e_help\n\n"
        "━━ P2 Django ━━\n/p2_root /invoices\n\n"
        "━━ P3 Ops ━━\n/p3_health /p3_root\n\n"
        "━━ P4 AI platform ━━\n/p4_health /p4_ready /p4_metrics\n"
        "/p4_search /p4_rerank — вектор + rerank\n"
        '/p4_rag "..." [top_k] [hybrid|lexical]\n'
        "/p4_ingest <src> текст… — sync\n/p4_ingest_async теж саме\n"
        "/p4_audit [limit] /p4_jobs [limit]\n/p4_job_new <source>\n/wiz або /ingest_wizard — діалог\n\n"
        "━━ P5 Retail ━━\n/p5_health /p5_metrics\n/p5_revenue [days] /p5_skus [days] [limit]\n"
        "/p5_nlsql /p5_rag /p5_prompt /p5_sql /p5_compare\n\n"
        "Документ: надішліть .txt з підписом `src:tag` (опційно `|async` у підписі) для P4 ingest."
    )
    for part in chunk_text(text, TG_MAX):
        await update.message.reply_text(part)


async def cmd_cmds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    await cmd_help(update, context)


async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    u = update.effective_user
    c = update.effective_chat
    await update.message.reply_text(
        "Користувач:\n"
        f"user_id={u.id}\nusername=@{u.username or '–'}\nfull_name={(u.full_name or '')}\n\n"
        f"chat_id={c.id}\ntype={c.type}"
    )


async def cmd_dochelp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    await update.message.reply_text(
        "Надішліть документ текстом (.txt або text/plain).\n"
        "Підпис (caption) обовʼязковий, формат:\n"
        "`src:mysource`\nабо з чергою асинхронного ingest:\n"
        "`src:mysource |async`\n\n"
        f"Обмеження: до ~{settings.rate_limit_per_minute} текстових дій за хв (rate limit)."
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    hub: BackendHub = context.bot_data["hub"]
    lines = await _collect_status(settings, hub)
    await reply_text_safe(update, "\n".join(lines))


async def cmd_e2e_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    root = settings.e2e_project_root or "D:/Work/Python/Project1"
    msg = (
        "Project1 — UI E2E (pytest + selenium webdriver-manager).\n\n"
        "Приклад (PowerShell):\n"
        f"  cd {root}\n"
        "  py -m venv .venv\n"
        "  .\\.venv\\Scripts\\Activate.ps1\n"
        "  pip install -r requirements.txt\n"
        '  $env:PYTHONPATH="."\n'
        "  pytest --base-url https://www.saucedemo.com --headless\n\n"
        "Запуск E2E з Telegram не рекомендується; використовуйте CI або локально."
    )
    await update.message.reply_text(msg)


async def cmd_p2_root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project2_api_base:
        await update.message.reply_text("Задайте PROJECT2_API_BASE у .env")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.http_get_json(settings.project2_api_base.rstrip("/") + "/")
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(f"P2 root: {exc!s}")


async def cmd_invoices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project2_api_base or not settings.project2_jwt:
        await update.message.reply_text("Потрібні PROJECT2_API_BASE та PROJECT2_JWT у .env")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project2_list_invoices(settings.project2_api_base, settings.project2_jwt)
        await reply_json(update, context, settings, body, caption="/api/invoices/")
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p3_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    await _proj3_health_core(update, context, settings)


async def cmd_p3_root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    base = settings.project3_api_base
    if not base:
        await update.message.reply_text("Задайте PROJECT3_API_BASE")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project3_root(base)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def _proj3_health_core(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: Settings) -> None:
    if not settings.project3_api_base:
        await update.message.reply_text("Задайте PROJECT3_API_BASE")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project3_health(settings.project3_api_base)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _p4_health_kind(update, context, health=True)


async def cmd_p4_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _p4_health_kind(update, context, health=False)


async def _p4_health_kind(update: Update, context: ContextTypes.DEFAULT_TYPE, health: bool) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    base = settings.project4_api_base
    if not base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_health(base) if health else await hub.project4_ready(base)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    base = settings.project4_api_base
    if not base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        plain, ctype = await hub.project4_metrics_plain(base)
        bio_name = f"p4_metrics_{datetime.now(timezone.utc).strftime('%H%M%S')}.txt"
        await reply_bytes_document(update, plain.encode("utf-8"), bio_name, caption=ctype or "metrics")
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    base = settings.project5_api_base
    if not base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        plain, ctype = await hub.project5_metrics_plain(base)
        bio_name = f"p5_metrics_{datetime.now(timezone.utc).strftime('%H%M%S')}.txt"
        await reply_bytes_document(update, plain.encode("utf-8"), bio_name, caption=ctype or "metrics")
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    raw = " ".join(context.args or []).strip()
    if not raw:
        await update.message.reply_text("Використання: /p4_search <запит> [limit]")
        return
    parts = shlex.split(raw)
    limit = 5
    if len(parts) >= 2 and parts[-1].isdigit():
        limit = int(parts.pop())
    q = " ".join(parts)
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_search(settings.project4_api_base, q, limit=limit)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_rerank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    raw = " ".join(context.args or []).strip()
    if not raw:
        await update.message.reply_text(
            "Використання: /p4_rerank <q> [limit] [retrieval_limit] [hybrid|lexical]"
        )
        return
    try:
        parts = shlex.split(raw)
    except ValueError as exc:
        await update.message.reply_text(f"Шелл-помилка: {exc}")
        return
    strategy = "hybrid"
    if parts and parts[-1] in ("hybrid", "lexical"):
        strategy = parts.pop()
    rlim = 15
    if parts and parts[-1].isdigit():
        rlim = int(parts.pop())
    lim = 5
    if parts and parts[-1].isdigit():
        lim = int(parts.pop())
    q = " ".join(parts)
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_search_rerank(
            settings.project4_api_base, q=q, limit=lim, retrieval_limit=rlim, strategy=strategy
        )
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_rag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    raw = " ".join(context.args or []).strip()
    if not raw:
        await update.message.reply_text('Використання: /p4_rag "питання" [top_k] [hybrid|lexical]')
        return
    try:
        parts = shlex.split(raw)
    except ValueError as exc:
        await update.message.reply_text(f"Шелл-помилка: {exc}")
        return
    strategy = "hybrid"
    top_k = 5
    if parts and parts[-1] in ("hybrid", "lexical"):
        strategy = parts.pop()
    if parts and parts[-1].isdigit():
        top_k = int(parts.pop())
    question = " ".join(parts)
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_rag(settings.project4_api_base, question, top_k=top_k, strategy=strategy)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_ingest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _p4_ingest_core(update, context, sync=True)


async def cmd_p4_ingest_async(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _p4_ingest_core(update, context, sync=False)


async def _p4_ingest_core(update: Update, context: ContextTypes.DEFAULT_TYPE, sync: bool) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    raw = " ".join(context.args or "").strip()
    if not raw:
        await update.message.reply_text("Використання: /<cmd> <source> <довгий текст…>")
        return
    head, _, tail = raw.partition(" ")
    source = head.strip()
    text = tail.strip()
    if not source or not text:
        await update.message.reply_text("Потрібні source і текст.")
        return
    hub: BackendHub = context.bot_data["hub"]
    base = settings.project4_api_base
    try:
        if sync:
            body = await hub.project4_ingest(base, source, text)
        else:
            body = await hub.project4_ingest_async(base, source, text)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    limit = 10
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_ops_jobs(settings.project4_api_base, limit=limit)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_audit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    limit = 20
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_ops_audit(settings.project4_api_base, limit=limit)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p4_job_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    name = " ".join(context.args or []).strip()
    if not settings.project4_api_base:
        await update.message.reply_text("Задайте PROJECT4_API_BASE")
        return
    if not name:
        await update.message.reply_text("/p4_job_new <source_name>")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project4_ops_create_job(settings.project4_api_base, name)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    base = settings.project5_api_base
    if not base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_health(base)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    days = 30
    if context.args and context.args[0].isdigit():
        days = int(context.args[0])
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_revenue(settings.project5_api_base, days=days)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_skus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    days = 30
    limit = 10
    if len(context.args) >= 1 and context.args[0].isdigit():
        days = int(context.args[0])
    if len(context.args) >= 2 and context.args[1].isdigit():
        limit = int(context.args[1])
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_top_skus(settings.project5_api_base, days=days, limit=limit)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_nlsql(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    question = " ".join(context.args or "").strip()
    if not question:
        await update.message.reply_text("/p5_nlsql <бізнес-питання>")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_nl_sql(settings.project5_api_base, question)
        txt = pretty_json(body)
        for part in chunk_text(txt, TG_MAX):
            await update.message.reply_text(part)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_rag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    question = " ".join(context.args or "").strip()
    if not question:
        await update.message.reply_text("/p5_rag <питання>")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_rag(settings.project5_api_base, question)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    raw = " ".join(context.args or "").strip()
    if not raw:
        await update.message.reply_text('/p5_prompt "<task>" | optional context')
        return
    parts = raw.split("|", 1)
    task = parts[0].strip()
    context_txt = parts[1].strip() if len(parts) > 1 else ""
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_prompt_run(settings.project5_api_base, task, context=context_txt)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_sql(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    sql = " ".join(context.args or "").strip()
    if not sql:
        await update.message.reply_text("/p5_sql SELECT …")
        return
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_safe_sql(settings.project5_api_base, sql)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def cmd_p5_compare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if not settings.project5_api_base:
        await update.message.reply_text("Задайте PROJECT5_API_BASE")
        return
    raw = " ".join(context.args or "").strip()
    if not raw:
        await update.message.reply_text('/p5_compare "<task>" | контекст | mock openai …')
        return
    chunks = [c.strip() for c in raw.split("|")]
    task = chunks[0] if chunks else ""
    context_txt = chunks[1] if len(chunks) > 1 else ""
    providers = ["mock", "openai", "claude"]
    if len(chunks) >= 3 and chunks[2]:
        providers = chunks[2].split()
        if not providers:
            providers = ["mock"]
    hub: BackendHub = context.bot_data["hub"]
    try:
        body = await hub.project5_prompt_compare(settings.project5_api_base, task, context_txt, providers)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def wiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return ConversationHandler.END
    if not settings.project4_api_base:
        await update.message.reply_text("Потрібен PROJECT4_API_BASE")
        return ConversationHandler.END
    context.user_data["in_wiz"] = True
    await update.message.reply_text(
        "Майстер P4 ingest.\n"
        "Крок 1/2 — один рядок `source_name`.\nСкасування: /cancel\n"
        "Під час майстра лише текст (без вкладень)."
    )
    return W_SRC


async def wiz_src(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = (update.message.text or "").strip()
    if raw in REPLY_NAV_LABELS:
        await update.message.reply_text("Спочатку /cancel, щоб вийти з майстра та натискати кнопки.")
        return W_SRC
    context.user_data["p4_src"] = raw
    await update.message.reply_text("Крок 2/2 — вставте весь текст для індексації одним повідомленням.")
    return W_TXT


async def wiz_txt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    settings: Settings = context.bot_data["settings"]
    hub: BackendHub = context.bot_data["hub"]
    blob = (update.message.text or "").strip()
    if blob in REPLY_NAV_LABELS:
        await update.message.reply_text("Спочатку /cancel.")
        return W_TXT
    src = context.user_data.get("p4_src")
    try:
        if not src:
            await update.message.reply_text("Втрачено source. Запустіть /wiz знову.")
            return ConversationHandler.END
        base = settings.project4_api_base
        if not base:
            await update.message.reply_text("Немає PROJECT4_API_BASE")
            return ConversationHandler.END
        body = await hub.project4_ingest(base, str(src), blob)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))
    finally:
        context.user_data.pop("p4_src", None)
        context.user_data.pop("in_wiz", None)
    return ConversationHandler.END


async def wiz_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("p4_src", None)
    context.user_data.pop("in_wiz", None)
    await update.message.reply_text("Зупинено.")
    return ConversationHandler.END


async def on_plain_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    if context.user_data.get("in_wiz"):
        await update.message.reply_text("Завершіть /wiz або /cancel, потім надсилайте файли.")
        return
    if not settings.project4_api_base:
        await update.message.reply_text("PROJECT4_API_BASE не заданий.")
        return
    doc = update.message.document
    if doc.file_size and doc.file_size > 18 * 1024 * 1024:
        await update.message.reply_text("Файл завеликий (>18 MB).")
        return
    mime = doc.mime_type or ""
    fname = doc.file_name or ""
    ok = mime == "text/plain" or fname.lower().endswith(".txt") or mime.endswith("csv")
    if not ok:
        await update.message.reply_text("Приймаю лише text/plain або .txt (.csv експериментально).")
        return
    caption = update.message.caption or ""
    m = re.search(r"src:([^\s|]+)", caption, flags=re.IGNORECASE)
    if not m:
        await update.message.reply_text("У підписі до файлу обовʼязково є `src:tag`.\n`/dochelp`")
        return
    source = m.group(1).strip()
    use_async = "|async" in caption.lower() or "|queue" in caption.lower()
    fobj = await context.bot.get_file(doc.file_id)
    buf = bytes(await fobj.download_as_bytearray())
    text_body = buf.decode("utf-8", errors="replace")
    hub: BackendHub = context.bot_data["hub"]
    base = settings.project4_api_base
    try:
        if use_async:
            body = await hub.project4_ingest_async(base, source, text_body)
        else:
            body = await hub.project4_ingest(base, source, text_body)
        await reply_json(update, context, settings, body)
    except Exception as exc:
        await update.message.reply_text(str(exc))


async def on_web_app_data_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    raw = update.message.web_app_data.data if update.message.web_app_data else "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await update.message.reply_text(f"Некоректний JSON з Mini App:\n{raw[:1200]}")
        return
    action = payload.get("action")
    if action == "webapp_ping":
        await update.message.reply_text(f"Mini App ping OK · t={payload.get('t')}")
    elif action == "webapp_status_digest":
        await cmd_status(update, context)
    else:
        await update.message.reply_text(
            f"Невідома дія Mini App: {action!r}\n" + pretty_json(payload)[:TG_MAX]
        )


async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await guard_request(update, context, settings):
        return
    await update.message.reply_text("Невідома команда. Використайте /cmds")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Необроблена помилка: %s", context.error)


async def watchdog_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not settings.enable_watchdog:
        return
    targets = admin_chat_ids(settings)
    if not targets:
        return
    hub: BackendHub = context.application.bot_data["hub"]
    lines = await _collect_status(settings, hub)
    text = "\n".join(lines)[:TG_MAX]
    bot = context.application.bot
    for cid in targets:
        try:
            await bot.send_message(chat_id=cid, text=text)
        except Exception:
            logger.warning("Не вдалося надіслати watchdog у chat_id=%s", cid, exc_info=True)


def build_application(settings: Settings, hub: BackendHub) -> Application:
    async def _close_hub(application: Application) -> None:
        await hub.aclose()

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(bootstrap_post_init)
        .post_shutdown(_close_hub)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["hub"] = hub

    conv = ConversationHandler(
        entry_points=[CommandHandler("ingest_wizard", wiz_start), CommandHandler("wiz", wiz_start)],
        states={
            W_SRC: [MessageHandler(filters.TEXT & ~filters.COMMAND, wiz_src)],
            W_TXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, wiz_txt)],
        },
        fallbacks=[CommandHandler("cancel", wiz_cancel)],
        allow_reentry=True,
    )

    handlers = [
        conv,
        CallbackQueryHandler(on_menu_callback, pattern=r"^(m\||a\||2\||3\||4\||5\|)"),
        MessageHandler(web_app_payload_filter, on_web_app_data_message),
        MessageHandler(reply_nav_filter, route_reply_navigation),
        MessageHandler(filters.Document.ALL, on_plain_document),
        CommandHandler("start", cmd_start),
        CommandHandler("help", cmd_help),
        CommandHandler("cmds", cmd_cmds),
        CommandHandler("whoami", cmd_whoami),
        CommandHandler("dochelp", cmd_dochelp),
        CommandHandler("keyboard", cmd_keyboard),
        CommandHandler("hide_kb", cmd_hide_kb),
        CommandHandler("panel", cmd_panel),
        CommandHandler("status", cmd_status),
        CommandHandler("e2e_help", cmd_e2e_help),
        CommandHandler("p2_root", cmd_p2_root),
        CommandHandler("invoices", cmd_invoices),
        CommandHandler("p3_health", cmd_p3_health),
        CommandHandler("p3_root", cmd_p3_root),
        CommandHandler("p4_health", cmd_p4_health),
        CommandHandler("p4_ready", cmd_p4_ready),
        CommandHandler("p4_metrics", cmd_p4_metrics),
        CommandHandler("p5_metrics", cmd_p5_metrics),
        CommandHandler("p4_search", cmd_p4_search),
        CommandHandler("p4_rerank", cmd_p4_rerank),
        CommandHandler("p4_rag", cmd_p4_rag),
        CommandHandler("p4_ingest", cmd_p4_ingest),
        CommandHandler("p4_ingest_async", cmd_p4_ingest_async),
        CommandHandler("p4_jobs", cmd_p4_jobs),
        CommandHandler("p4_audit", cmd_p4_audit),
        CommandHandler("p4_job_new", cmd_p4_job_new),
        CommandHandler("p5_health", cmd_p5_health),
        CommandHandler("p5_revenue", cmd_p5_revenue),
        CommandHandler("p5_skus", cmd_p5_skus),
        CommandHandler("p5_nlsql", cmd_p5_nlsql),
        CommandHandler("p5_rag", cmd_p5_rag),
        CommandHandler("p5_prompt", cmd_p5_prompt),
        CommandHandler("p5_sql", cmd_p5_sql),
        CommandHandler("p5_compare", cmd_p5_compare),
    ]
    for h in handlers:
        application.add_handler(h)
    application.add_handler(MessageHandler(filters.COMMAND, cmd_unknown))

    jq = getattr(application, "job_queue", None)
    if jq and settings.enable_watchdog and admin_chat_ids(settings):
        jq.run_repeating(
            watchdog_job,
            interval=float(settings.watchdog_interval_seconds),
            first=35,
            name="hub_watchdog",
        )

    application.add_error_handler(error_handler)
    return application


def main() -> None:
    settings = get_settings()
    if settings.serve_web_app_locally:
        from telegram_hub.webapp_server import run_uvicorn_sync

        threading.Thread(
            target=run_uvicorn_sync,
            kwargs={
                "host": settings.web_app_bind_host,
                "port": settings.web_app_bind_port,
            },
            daemon=True,
            name="petlab-webapp",
        ).start()
        logger.info(
            "Локальний Mini App: http://%s:%s/ (додайте HTTPS-тунель у TELEGRAM_WEB_APP_URL)",
            settings.web_app_bind_host,
            settings.web_app_bind_port,
        )
    hub = BackendHub(max_retries=settings.http_max_retries, backoff_seconds=settings.http_backoff_seconds)
    application = build_application(settings, hub)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
