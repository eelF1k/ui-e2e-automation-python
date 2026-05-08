from __future__ import annotations

import logging

from telegram import BotCommand, MenuButtonCommands, MenuButtonWebApp, WebAppInfo
from telegram.ext import Application

from telegram_hub.config import Settings

logger = logging.getLogger(__name__)


BOT_COMMANDS: list[tuple[str, str]] = [
    ("start", "Меню та клавіатури"),
    ("status", "Статус бекендів"),
    ("help", "Повний опис команд"),
    ("cmds", "Те саме що /help"),
    ("whoami", "Мій Telegram id"),
    ("dochelp", "Як надсилати .txt на ingest"),
    ("wiz", "Майстер P4 ingest"),
    ("keyboard", "Показати reply-клавіатуру"),
    ("hide_kb", "Сховати reply-клавіатуру"),
    ("panel", "Посилання на Web-панель"),
    ("p2_root", "Django корінь"),
    ("invoices", "Інвойси JWT"),
    ("p3_health", "Banking health"),
    ("p3_root", "Banking /"),
    ("p4_health", "AI platform health"),
    ("p5_health", "Retail health"),
]


async def post_init(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]

    cmds = [BotCommand(c, desc) for c, desc in BOT_COMMANDS]
    await application.bot.set_my_commands(cmds)

    url = (settings.telegram_web_app_url or "").strip()
    if url:
        try:
            await application.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text=settings.telegram_web_app_menu_text,
                    web_app=WebAppInfo(url=url),
                ),
            )
            logger.info("Menu button WebApp: %s…", url[:64])
        except Exception as exc:
            logger.warning("Не вдалося встановити WebApp меню: %s — лишаємо Commands", exc)
            await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    else:
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logger.info("Menu button: лише список команд (нема TELEGRAM_WEB_APP_URL)")

