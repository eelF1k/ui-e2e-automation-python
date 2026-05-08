"""Клавіатури: inline (callback) + reply (нижня панель) + WebApp."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

# Reply-клавіатура: збіг тексту в main.route_reply_button
LBL_STATUS = "📊 Статус"
LBL_HELP = "❓ Допомога"
LBL_INLINE = "📲 Inline-меню"
LBL_P4 = "🟣 P4 RAG"
LBL_P5 = "🟢 P5 Retail"
LBL_WIZ = "🧩 Майстер ingest"
LBL_PANEL = "🖥 Web-панель"
LBL_HIDE = "⌧ Сховати клав."

REPLY_NAV_LABELS = frozenset(
    {
        LBL_STATUS,
        LBL_HELP,
        LBL_INLINE,
        LBL_P4,
        LBL_P5,
        LBL_WIZ,
        LBL_PANEL,
        LBL_HIDE,
    }
)


def kb_main(*, web_app_url: str = "") -> InlineKeyboardMarkup:
    wa = (web_app_url or "").strip()
    row_web: list[InlineKeyboardButton] = []
    if wa:
        row_web = [InlineKeyboardButton("🌐 Mini App", web_app=WebAppInfo(url=wa))]
    grid = [
        [
            InlineKeyboardButton("P5 Retail", callback_data="m|p5"),
            InlineKeyboardButton("P4 RAG", callback_data="m|p4"),
        ],
        [
            InlineKeyboardButton("P3 Ops", callback_data="m|p3"),
            InlineKeyboardButton("P2 SaaS", callback_data="m|p2"),
        ],
        [
            InlineKeyboardButton("Статус сервісів", callback_data="a|stat"),
            InlineKeyboardButton("Допомога", callback_data="a|help"),
        ],
        [InlineKeyboardButton("Майстер ingest (P4)", callback_data="a|wiz")],
    ]
    if row_web:
        grid.insert(0, row_web)
    return InlineKeyboardMarkup(grid)


def kb_reply(*, web_app_url: str = "") -> ReplyKeyboardMarkup:
    """Нижня «сильна» панель швидких дій."""
    wa = (web_app_url or "").strip()
    panel_btn: KeyboardButton | None = None
    if wa:
        panel_btn = KeyboardButton(LBL_PANEL, web_app=WebAppInfo(url=wa))

    row1 = [KeyboardButton(LBL_STATUS), KeyboardButton(LBL_HELP)]
    row2 = [KeyboardButton(LBL_INLINE), KeyboardButton(LBL_WIZ)]
    row3 = [KeyboardButton(LBL_P4), KeyboardButton(LBL_P5)]
    rows = [row1, row2, row3]
    if panel_btn:
        rows.append([panel_btn])
    rows.append([KeyboardButton(LBL_HIDE)])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Команди або кнопки…",
    )


def kb_p4() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Health", callback_data="4|hl"),
                InlineKeyboardButton("Ready", callback_data="4|rd"),
                InlineKeyboardButton("Metrics", callback_data="4|mt"),
            ],
            [
                InlineKeyboardButton("Jobs", callback_data="4|jb"),
                InlineKeyboardButton("Audit", callback_data="4|au"),
            ],
            [InlineKeyboardButton("← Назад", callback_data="m|hm")],
        ]
    )


def kb_p5() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Health", callback_data="5|hl"),
                InlineKeyboardButton("Metrics", callback_data="5|mt"),
            ],
            [
                InlineKeyboardButton("Revenue 7d", callback_data="5|rv7"),
                InlineKeyboardButton("Top SKU 7d", callback_data="5|sk7"),
            ],
            [InlineKeyboardButton("← Назад", callback_data="m|hm")],
        ]
    )


def kb_p3() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Health", callback_data="3|hl"),
                InlineKeyboardButton("Root", callback_data="3|rt"),
            ],
            [InlineKeyboardButton("← Назад", callback_data="m|hm")],
        ]
    )


def kb_p2() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Root Django", callback_data="2|rt"),
                InlineKeyboardButton("Інвойси", callback_data="2|in"),
            ],
            [InlineKeyboardButton("← Назад", callback_data="m|hm")],
        ]
    )
