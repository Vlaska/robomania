from __future__ import annotations

from typing import TYPE_CHECKING

from disnake import ApplicationCommandInteraction  # noqa: F401
from disnake.ext import commands

if TYPE_CHECKING:
    from robomania.bot import Robomania


class DiceCog(commands.Cog):
    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

    def parse_dice(self, dice: str) -> None:
        pass

    # @commands.slash_command()
    # async def roll(
    #     self,
    #     inter: ApplicationCommandInteraction,
    #     dice: list[str]
    # ) -> None:
    #     pass
