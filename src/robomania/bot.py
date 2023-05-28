from __future__ import annotations

import contextlib
import logging
from contextvars import ContextVar
from importlib import resources
from pathlib import Path
from typing import Generator, Protocol, cast

import disnake
import pytz
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database

from robomania.config import Settings, settings
from robomania.locale import DefaultLocale
from robomania.utils.exceptions import NoInstanceError
from robomania.utils.healthcheck import HealthcheckClient

intents = disnake.Intents.default()
intents.typing = False
intents.message_content = True


class Translator(Protocol):
    def __call__(self, key: str, default: str | None = None) -> str:
        pass


class Robomania(commands.Bot):
    client: AsyncIOMotorClient
    settings: Settings = settings
    __bot: Robomania
    __blocking_db_counter = 0
    timezone = pytz.timezone("Europe/Warsaw")

    _current_locale = ContextVar(
        "_current_locale",
        default=disnake.enums.Locale.en_GB,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__class__.__bot = self

    def setup(self) -> None:
        with resources.path("robomania", "locale") as locale_path:
            self.i18n.load(locale_path)
        self.client = AsyncIOMotorClient(str(settings.db_url))

        if settings.debug:
            logger.warning("Running in DEBUG mode.")
            self.reload = True
            self._sync_commands_debug = True
            self._test_guilds = (958823316850880512,)

    @contextlib.contextmanager
    def blocking_db(self) -> Generator[MongoClient, None, None]:
        if self.__blocking_db_counter == 0:
            async_client = self.client
            self.client = MongoClient(str(settings.db_url))

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
            self.loop.set_debug(True)

        self.healthcheck_client = await HealthcheckClient.start(self)
        await super().start(*args, **kwargs)

    async def close(self) -> None:
        await self.healthcheck_client.shutdown()
        await super().close()

    def get_db(self, name: str) -> Database:
        if settings.environment:
            name = f"{name}-{settings.environment}"
        return self.client[name]

    @classmethod
    def get_bot(cls) -> Robomania:
        try:
            return cls.__bot
        except AttributeError:
            raise NoInstanceError("No bot instance was created.")

    @classmethod
    def tr(cls, key: str, default: str | None = None) -> str:
        bot = cls.get_bot()
        locale = cls._current_locale.get()

        logger.debug(f'Get translation: {{"{locale}": "{key}"}}')
        try:
            translations = bot.i18n.get(key)
            assert translations
            value = translations.get(locale.value, None)
        except (disnake.LocalizationKeyError, AttributeError):
            logger.warning(f'Missing localization for key: "{key}"')
            value = None

        if value is None and default:
            return default

        if value is None:
            logger.warning(
                f'Missing localization for key: "{key}" for "{locale}" locale'
            )
            value = DefaultLocale.get(key)

        return value

    @classmethod
    @contextlib.contextmanager
    def localize(
        cls, locale: disnake.enums.Locale
    ) -> Generator[Translator, None, None]:
        token = cls._current_locale.set(locale)
        try:
            yield cls.tr
        finally:
            cls._current_locale.reset(token)


bot = Robomania(
    ">",
    case_insensitive=True,
    intents=intents,
)


logger = logging.getLogger("robomania")


def init_logger(logger: logging.Logger, out_file: str) -> None:
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    log_folder = settings.log_folder
    log_folder.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")

    file_handler = logging.FileHandler(
        log_folder / out_file, encoding="utf-8", mode="a"
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


@bot.event
async def on_ready():
    logger.info(f'We have logged in as "{bot.user}"')


def configure_bot(config_path: str | Path = ".env") -> None:
    init_logger(logger, "robomania.log")
    init_logger(logging.getLogger("disnake"), "disnake.log")

    bot.setup()

    for extension in settings.load_extensions:
        bot.load_extension(extension)


def main() -> None:
    bot.run(settings.discord_token.get_secret_value())


if __name__ == "__main__":
    configure_bot()
    main()
