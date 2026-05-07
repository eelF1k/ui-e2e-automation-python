TG_MAX_MESSAGE = 4000


def chunk_text(text: str, limit: int = TG_MAX_MESSAGE) -> list[str]:
    text = text or ""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + limit])
        start += limit
    return chunks


def html_escape(s: object) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def fmt_kv(data: dict) -> str:
    lines = []
    for k, v in data.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)
