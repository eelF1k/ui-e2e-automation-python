from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    telegram_allowed_user_ids: str = Field(
        default="",
        description="Через кому: 123,456. Порожньо = усі користувачі.",
    )
    telegram_admin_chat_ids: str = Field(
        default="",
        description="Через кому: chat/user id для watchdog-сповіщень.",
    )

    http_max_retries: int = Field(default=3, ge=0, le=10)
    http_backoff_seconds: float = Field(default=0.5, ge=0.05)

    rate_limit_per_minute: int = Field(default=45, ge=5, le=240)
    heavy_json_as_file_over_bytes: int = Field(default=3400, ge=512)

    enable_watchdog: bool = Field(default=False)
    watchdog_interval_seconds: int = Field(default=900, ge=60)

    project2_api_base: str = ""
    project2_jwt: str = ""

    project3_api_base: str = ""

    project4_api_base: str = ""

    project5_api_base: str = ""

    e2e_project_root: str = Field(
        default="",
        description="Корінь проєкту UI E2E (Project1).",
    )

    # Mini App (HTTPS). Для телефонів зазвичай потрібен публічний URL (Cloudflare Tunnel / ngrok).
    telegram_web_app_url: str = Field(
        default="",
        description="Повна HTTPS-URL головної Mini App, напр. https://xxx.trycloudflare.com/",
    )
    telegram_web_app_menu_text: str = Field(default="Панель", description="Підпис кнопки меню WebApp")

    serve_web_app_locally: bool = Field(
        default=False,
        description="Підняти starlette/uvicorn локально (узгодьте з тунелем).",
    )
    web_app_bind_host: str = "127.0.0.1"
    web_app_bind_port: int = Field(default=8787, ge=1, le=65535)


@lru_cache
def get_settings() -> Settings:
    return Settings()
