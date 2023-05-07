from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import (
    AnyHttpUrl,
    BaseSettings,
    Extra,
    Field,
    MongoDsn,
    SecretStr,
    validator,
)


class BasicSettings(BaseSettings, extra=Extra.allow):
    debug: bool = Field(default=False)


class Settings(BasicSettings):
    discord_token: SecretStr

    db_username: str
    db_password: SecretStr
    db_auth_db: str = ""
    db_host: str
    db_port: str | None = None

    db_url: MongoDsn | None = None

    @validator("db_url")
    def validate_url(
        cls, v: str | None, values: dict[str, Any]
    ) -> MongoDsn:  # noqa: N805
        if isinstance(v, MongoDsn):
            return v

        username = values["db_username"]
        password: SecretStr = values["db_password"]

        host = values["db_host"]
        port = values["db_port"]
        auth_db = f"/{values['db_auth_db']}"

        if port:
            protocol = "mongodb"
        else:
            protocol = "mongodb+srv"

        return MongoDsn.build(
            scheme=protocol,
            user=username,
            password=password.get_secret_value(),
            host=host,
            port=port,
            path=auth_db,
            query="retryWrites=true&w=majority",
        )

    scraper_user_agent: str | None = None
    facebook_cookies_path: Path
    log_folder: Path

    announcements_target_channel: int
    picrew_target_channel: int
    scraping_service_url: str

    time_betweent_announcements_check: int = 10

    asset_base_url: AnyHttpUrl

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings: Settings

if "pytest" in sys.modules:
    settings = BasicSettings()  # type: ignore
else:
    settings = Settings()
