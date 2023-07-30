from __future__ import annotations

from typing import TYPE_CHECKING, cast

from disnake import Embed
from disnake.ext import commands

from robomania.utils.types import GuildMessageable

if TYPE_CHECKING:
    from disnake.interactions.application_command import ApplicationCommandInteraction

    from robomania.bot import Robomania

# @bot.event
# async def on_message(message):
#     if message.author == bot.user:

#     if message.content.startswith('>hello'):


class Tester(commands.Cog):
    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

    @commands.command(name="world")
    async def test(self, ctx: commands.Context):
        await ctx.send("Hello world!")

    @commands.slash_command(
        name="purge",
        guild_ids=[
            958823316850880512,  # Test server
        ],
    )
    @commands.is_owner()
    async def purge(self, inter: ApplicationCommandInteraction, messages: int):
        await inter.response.defer()
        deleted = await cast(GuildMessageable, inter.channel).purge(
            limit=messages, before=inter.created_at
        )
        await inter.followup.send(f"Deleted {len(deleted)} messages.", delete_after=5)

    @commands.slash_command()
    @commands.is_owner()
    async def reload(self, inter: ApplicationCommandInteraction, extension: str):
        self.bot.reload_extension(f"cogs.{extension}")

        embed = Embed(
            title="Reload",
            description=f"{extension} successfully reloaded",
            color=0xFF00C8,
        )
        await inter.send(embed=embed)


def setup(bot: Robomania):
    bot.add_cog(Tester(bot))
