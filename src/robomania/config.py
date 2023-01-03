from __future__ import annotations

import os
import sys
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, Type, get_args, get_type_hints

import dotenv
from pydantic import BaseSettings, Extra, Field, MongoDsn, SecretStr, validator


class Config:
    token: Annotated[str, 'DISCORD_TOKEN']
    db_username: Annotated[str, 'DB_USERNAME']
    db_password: Annotated[str, 'DB_PASSWORD']
    db_auth_db: Annotated[str, 'DB_AUTH_DB', '']
    db_host: Annotated[str, 'DB_HOST']
    db_port: Annotated[int, 'DB_PORT', 0]
    announcements_target_channel: Annotated[
        int,
        'ANNOUNCEMENTS_TARGET_CHANNEL'
    ]
    picrew_target_channel: Annotated[
        int,
        'PICREW_TARGET_CHANNEL'
    ]
    scraper_user_agent: Annotated[str, 'FACEBOOK_SCRAPER_USER_AGENT']
    facebook_cookies_path: Annotated[str, 'FACEBOOK_COOKIES_PATH']
    log_folder: Annotated[Path, 'LOG_FOLDER', Path('.')]

    debug: Annotated[bool, 'DEBUG', False]

    @classmethod
    def load_env(cls, path: str | Path, stream: StringIO = None) -> None:
        if stream:
            dotenv.load_dotenv(stream=stream)
        else:
            dotenv.load_dotenv(path)

        cls._load_values()

    @classmethod
    def _load_values(cls) -> None:
        _type: Type[Any]
        name: str
        value: Any

        for k, v in get_type_hints(cls, include_extras=True).items():
            _type, name, *rest = get_args(v)

            value = os.environ.get(name)

            if value is None:
                if rest:
                    value = rest[0]
            elif _type is bool:
                if isinstance(value, str):
                    value = value.lower() in {'1', 'true', 'yes'}
            else:
                value = _type(value)

            setattr(cls, k, value)


class BasicSettings(BaseSettings, extra=Extra.allow):
    debug: bool = Field(default=False)


class Settings(BasicSettings):
    discord_token: SecretStr

    db_username: str
    db_password: SecretStr
    db_auth_db: str = ''
    db_host: str
    db_port: str | None = None

    db_url: MongoDsn | None = None

    @validator('db_url')
    def validate_url(
        cls,  # noqa: N805
        v: str | None,
        values: dict[str, Any]
    ) -> MongoDsn:
        if isinstance(v, MongoDsn):
            return v

        username = values['db_username']
        password: SecretStr = values['db_password']

        host = values['db_host']
        port = values['db_port']
        auth_db = f"/{values['db_auth_db']}"

        if port:
            protocol = 'mongodb'
        else:
            protocol = 'mongodb+srv'

        return MongoDsn.build(
            scheme=protocol,
            user=username,
            password=password.get_secret_value(),
            host=host,
            port=port,
            path=auth_db,
            query='retryWrites=true&w=majority'
        )

    scraper_user_agent: str | None = None
    facebook_cookies_path: Path
    log_folder: Path

    announcements_target_channel: int
    picrew_target_channel: int

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings: Settings

if 'pytest' in sys.modules:
    settings = BasicSettings()  # type: ignore
else:
    settings = Settings()
