"""
Starlette: спочатку /health, решта — статика з index.html.
"""

from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse

_STATIC_DIR = Path(__file__).resolve().parent / "webapp_static"


async def health(_request):
    return JSONResponse({"ok": True, "service": "petlab-webapp"})


def build_starlette_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/api/health", health, methods=["GET"]),
            Mount(
                "/",
                StaticFiles(directory=str(_STATIC_DIR), html=True),
                name="web",
            ),
        ],
    )


def run_uvicorn_sync(host: str = "127.0.0.1", port: int = 8787) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Установіть uvicorn і starlette — див. requirements.txt") from exc

    uvicorn.run(build_starlette_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    import sys

    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8787
    run_uvicorn_sync(host=h, port=p)
