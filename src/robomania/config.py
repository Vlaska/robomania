from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import disnake
from pydantic import (
    AnyHttpUrl,
    Field,
    FieldValidationInfo,
    MongoDsn,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from pathlib import Path


class BasicSettings(BaseSettings):
    debug: bool = Field(default=False)

    model_config = SettingsConfigDict(extra="allow")


class Settings(BasicSettings):
    discord_token: SecretStr
    environment: str = ""

    db_username: str
    db_password: SecretStr
    db_auth_db: str = ""
    db_host: str
    db_port: str | None = None

    db_url: MongoDsn | None = None

    @field_validator("db_url")
    @classmethod
    def validate_url(cls, v: str | None, info: FieldValidationInfo) -> str:
        if v:
            return v

        username = info.data["db_username"]
        password: SecretStr = info.data["db_password"]

        host = info.data["db_host"]
        port = info.data["db_port"]
        auth_db = f"/{info.data['db_auth_db']}"

        if port:
            protocol = "mongodb"
            port = f":{port}"
        else:
            protocol = "mongodb+srv"

        return f"{protocol}://{username}:{password}@{host}{port}/{auth_db}?retryWrites=true&w=majority"

    scraper_user_agent: str | None = None
    facebook_cookies_path: Path
    log_folder: Path

    announcements_target_channel: int
    picrew_target_channel: int
    scraping_service_url: str = ""

    time_betweent_announcements_check: int = 10

    assets_base_url: AnyHttpUrl

    load_extensions: tuple[str, ...] = (
        "robomania.cogs.announcements",
        "robomania.cogs.picrew",
        "robomania.cogs.dice",
        "robomania.cogs.poll",
        "robomania.cogs.info",
    )

    default_locale: disnake.Locale = disnake.Locale.en_GB

    available_locales: tuple[str, ...] = (
        "pl",
        "en_GB",
        "en_US",
    )
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings: Settings

if "pytest" in sys.modules:
    settings = BasicSettings()  # type: ignore
else:
    settings = Settings()
