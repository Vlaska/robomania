# type: ignore[name-defined]
from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Callable, Generator, cast

import disnake
import pytz
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database

from robomania.config import Settings, settings
from robomania.locale import DefaultLocale
from robomania.utils.exceptions import NoInstanceError

intents = disnake.Intents.default()
intents.typing = False
intents.message_content = True


class Robomania(commands.Bot):
    client: AsyncIOMotorClient
    announcements_last_checked: datetime = datetime(1, 1, 1)
    settings: Settings = settings
    __bot: Robomania
    __blocking_db_counter = 0
    timezone = pytz.timezone('Europe/Warsaw')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__class__.__bot = self

    def setup(self) -> None:
        locale_path = resources.path('robomania', 'locale')
        self.i18n.load(locale_path)
        self.client = AsyncIOMotorClient(str(settings.db_url))

        if settings.debug:
            self.reload = True
            self._sync_commands_debug = True
            self._test_guilds = [958823316850880512]

    @contextlib.contextmanager
    def blocking_db(self) -> Generator[MongoClient, None, None]:
        if self.__blocking_db_counter == 0:
            async_client = self.client
            self.client = MongoClient(self._get_db_connection_url())

        self.__blocking_db_counter += 1
        try:
            yield cast(MongoClient, self.client)
        finally:
            self.__blocking_db_counter -= 1
            if self.__blocking_db_counter == 0:
                self.client.close()
                self.client = async_client

    async def start(self, *args, **kwargs) -> None:
        if settings.debug:
            logger.warning('Running in debug mode')
            self.loop.set_debug(True)

        await super().start(*args, **kwargs)

    def get_db(self, name: str) -> Database:
        if settings.debug:
            name = f'{name}-dev'
        return self.client[name]

    @classmethod
    def get_bot(cls) -> Robomania:
        try:
            return cls.__bot
        except AttributeError:
            raise NoInstanceError('No bot instance was created.')

    def tr(
        self,
        key: str,
        locale: disnake.enums.Locale,
        default: str | None = None
    ) -> str:
        logger.debug(f'Get translation: {{"{locale}": "{key}"}}')
        try:
            translations = self.i18n.get(key)
            value = translations.get(locale.value, None)
        except (disnake.LocalizationKeyError, AttributeError):
            logger.warning(
                f'Missing localization for key: "{key}"'
            )
            value = None

        if value is None:
            logger.warning(
                f'Missing localization for key: "{key}" for "{locale}" locale'
            )
            value = DefaultLocale.get(key)

        if value == key and default:
            return default

        return value

    @contextlib.contextmanager
    def localize(
        self,
        locale: disnake.enums.Locale
    ) -> Generator[Callable[[str, str | None], str], None, None]:
        def tr(key: str, default: str | None = None) -> str:
            return self.tr(key, locale, default)

        yield tr


bot = Robomania(
    '>',
    case_insensitive=True,
    intents=intents,
)


logger = logging.getLogger('robomania')


def init_logger(logger: logging.Logger, out_file: str) -> None:
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    log_folder = settings.log_folder
    log_folder.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(
        log_folder / out_file,
        encoding='utf-8',
        mode='a'
    )
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
        )
    )
    logger.addHandler(handler)


@bot.event
async def on_ready():
    logger.info(f'We have logged in as "{bot.user}"')


def configure_bot(config_path: str | Path = '.env') -> None:
    init_logger(logger, 'robomania.log')
    init_logger(logging.getLogger('disnake'), 'disnake.log')

    bot.setup()

    # bot.load_extension('robomania.cogs.announcements')
    bot.load_extension('robomania.cogs.picrew')
    bot.load_extension('robomania.cogs.dice')

    if settings.debug:
        bot.load_extension('robomania.cogs.tester')


def main() -> None:
    bot.run(settings.discord_token.get_secret_value())


if __name__ == '__main__':
    configure_bot()
    main()
