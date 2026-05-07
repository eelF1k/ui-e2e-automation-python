"""Inline-меню: callback_data завжди < 64 символів (обмеження Telegram)."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
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
        [[InlineKeyboardButton("Health", callback_data="3|hl"), InlineKeyboardButton("Root", callback_data="3|rt")],
         [InlineKeyboardButton("← Назад", callback_data="m|hm")]])


def kb_p2() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Root Django", callback_data="2|rt"), InlineKeyboardButton("Інвойси", callback_data="2|in")],
         [InlineKeyboardButton("← Назад", callback_data="m|hm")]])
