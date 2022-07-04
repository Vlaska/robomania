from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, Type, get_args, get_type_hints

import dotenv


class Config:
    token: Annotated[str, 'DISCORD_TOKEN']
    db_username: Annotated[str, 'DB_USERNAME']
    db_password: Annotated[str, 'DB_PASSWORD']
    db_auth_db: Annotated[str, 'DB_AUTH_DB']
    db_host: Annotated[str, 'DB_HOST']
    db_port: Annotated[int, 'DB_PORT']
    announcements_target_channel: Annotated[
        int,
        'ANNOUNCEMENTS_TARGET_CHANNEL'
    ]
    scraper_user_agent: Annotated[str, 'FACEBOOK_SCRAPER_USER_AGENT']
    facebook_cookies_path: Annotated[str, 'FACEBOOK_COOKIES_PATH']

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
