from __future__ import annotations

import logging
import os
from datetime import datetime

import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from facebook_scraper import _scraper
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG = os.getenv('DEBUG', '0').lower() in {'1', 'true'}

if DEBUG:
    HOTRELOAD = True


intents = disnake.Intents.default()
intents.typing = False
intents.message_content = True
FACEBOOK_SCRAPER_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/99.0.4844.59 Mobile/15E148 Safari/604.1'


class Robomania(commands.Bot):
    client: AsyncIOMotorClient
    announcements_last_checked: datetime = datetime(1, 1, 1)

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

    async def start(self, *args, **kwargs) -> None:
        self.client = AsyncIOMotorClient(self._get_db_connection_url())

        _scraper.set_user_agent(FACEBOOK_SCRAPER_USER_AGENT)

        if DEBUG:
            logger.warning('Running in debug mode')
            self.loop.set_debug(True)

        await super().start(*args, **kwargs)

    def get_db(self, name: str) -> Database:
        return self.client[name]


bot = Robomania(
    '>',
    case_insensitive=True,
    intents=intents,
    reload=HOTRELOAD,
    test_guilds=[958823316850880512],
    sync_commands_debug=True
)


logger = logging.getLogger('robomania')


def init_logger(logger: logging.Logger, out_file: str) -> None:
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    handler = logging.FileHandler(out_file, encoding='utf-8', mode='a')
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
        )
    )
    logger.addHandler(handler)


@bot.event
async def on_ready():
    logger.info('We have logged in as "{0.user}"'.format(bot))


if DEBUG:
    @bot.slash_command(description='Test command')
    async def hello(inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message('World')

    @bot.command()
    @commands.is_owner()
    async def reload(ctx, extension):
        bot.reload_extension(f"cogs.{extension}")
        embed = disnake.Embed(
            title='Reload',
            description=f'{extension} successfully reloaded',
            color=0xff00c8)
        await ctx.send(embed=embed)


def main() -> None:
    init_logger(logger, 'robomania.log')
    init_logger(logging.getLogger('disnake'), 'disnake.log')

    bot.load_extension('robomania.cogs.announcements')
    if DEBUG:
        bot.load_extension('robomania.cogs.tester')

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
