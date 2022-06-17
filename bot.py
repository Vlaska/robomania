from __future__ import annotations
import os
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


@bot.event
async def on_ready():
    print('We have logged in as "{0.user}"'.format(bot))
    print(bot.cogs)


# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     if message.content.startswith('>hello'):
#         await message.channel.send('Hello!')

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


if __name__ == '__main__':
    bot.load_extension('cogs.tester')
    bot.load_extension('cogs.announcements')
    bot.run(TOKEN)
