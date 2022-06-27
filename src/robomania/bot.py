from __future__ import annotations
import os
import logging
from dotenv import load_dotenv

import disnake
from disnake.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
HOTRELOAD = os.getenv('HOTRELOAD', 'True') == 'True'

intents = disnake.Intents.default()
intents.typing = False
intents.message_content = True

bot = commands.Bot(
    '>',
    case_insensitive=True,
    intents=intents,
    reload=HOTRELOAD,
    test_guilds=[958823316850880512],
    sync_commands_debug=True
)


logger = logging.getLogger('disnake')


def init_logger() -> None:
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('disnake.log', encoding='utf-8', mode='w')
    handler.setFormatter(
        logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    )
    logger.addHandler(handler)


@bot.event
async def on_ready():
    print('We have logged in as "{0.user}"'.format(bot))
    print(bot.cogs)


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
    init_logger()
    bot.load_extension('robomania.cogs.tester')
    bot.load_extension('robomania.cogs.announcements')
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
