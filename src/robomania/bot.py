from __future__ import annotations

import contextlib
import logging
import os
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Generator, cast

import disnake
import pytz
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database

from robomania.config import Config
from robomania.utils.exceptions import NoInstanceError

intents = disnake.Intents.default()
intents.typing = False
intents.message_content = True


class Robomania(commands.Bot):
    client: AsyncIOMotorClient
    announcements_last_checked: datetime = datetime(1, 1, 1)
    config: Config
    __bot: Robomania
    __blocking_db_counter = 0
    timezone = pytz.timezone('Europe/Warsaw')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__class__.__bot = self

    @staticmethod
    def _get_db_connection_url() -> str:
        username = os.getenv('DB_USERNAME')
        password = os.getenv('DB_PASSWORD')

        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT', '')
        auth_db = os.getenv('DB_AUTH_DB', '')

        if port:
            port = f':{port}'
            protocol = 'mongodb'
        else:
            protocol = 'mongodb+srv'

        return (
            f'{protocol}://{username}:{password}@{host}{port}/{auth_db}?'
            'retryWrites=true&w=majority'
        )

    def setup(self) -> None:
        locale_path = resources.path('robomania', 'locale')
        self.i18n.load(locale_path)
        self.client = AsyncIOMotorClient(self._get_db_connection_url())

        if self.config.debug:
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

    @classmethod
    def load_config(cls, path: str | Path = '.env') -> None:
        cls.config = Config()
        cls.config.load_env(path)

    async def start(self, *args, **kwargs) -> None:
        if self.config.debug:
            logger.warning('Running in debug mode')
            self.loop.set_debug(True)

        await super().start(*args, **kwargs)

    def get_db(self, name: str) -> Database:
        if Config.debug:
            name = f'{name}-dev'
        return self.client[name]

    @classmethod
    def get_bot(cls) -> Robomania:
        try:
            return cls.__bot
        except AttributeError:
            raise NoInstanceError('No bot instance was created.')


bot = Robomania(
    '>',
    case_insensitive=True,
    intents=intents,
)


logger = logging.getLogger('robomania')


def init_logger(logger: logging.Logger, out_file: str) -> None:
    logger.setLevel(logging.DEBUG if Config.debug else logging.INFO)

    log_folder = Config.log_folder
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
    bot.load_config(config_path)

    init_logger(logger, 'robomania.log')
    init_logger(logging.getLogger('disnake'), 'disnake.log')

    bot.setup()

    bot.load_extension('robomania.cogs.announcements')
    bot.load_extension('robomania.cogs.picrew')
    if bot.config.debug:
        bot.load_extension('robomania.cogs.tester')


def main() -> None:
    bot.run(bot.config.token)


if __name__ == '__main__':
    configure_bot()
    main()
