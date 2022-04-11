from __future__ import annotations
import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot('>', case_insensitive=True)


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


@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    bot.reload_extension(f"cogs.{extension}")
    embed = discord.Embed(
        title='Reload',
        description=f'{extension} successfully reloaded',
        color=0xff00c8)
    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.load_extension('cogs.tester')
    bot.run(TOKEN)
