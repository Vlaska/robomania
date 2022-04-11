from __future__ import annotations

from discord.ext import commands

# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     if message.content.startswith('>hello'):
#         await message.channel.send('Hello!')


class Tester(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='world')
    async def test(self, ctx: commands.Context):
        await ctx.send('Hello world!')


def setup(bot: commands.Bot):
    bot.add_cog(Tester(bot))
