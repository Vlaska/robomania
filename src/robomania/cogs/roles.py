# flake8: noqa: F401
from __future__ import annotations

import enum
import logging
import random
from typing import TYPE_CHECKING

from disnake import AllowedMentions, Locale, Localised, Member, OptionChoice
from disnake.ext import commands
from disnake.interactions.application_command import ApplicationCommandInteraction

if TYPE_CHECKING:
    from disnake import Role

    from robomania.bot import Robomania


logger = logging.getLogger("robomania.cogs.roles")


class Roles(commands.Cog):
    def __init__(self, bot: Robomania):
        self.bot = bot

    @commands.slash_command()
    async def role(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @role.sub_command()
    async def new_role(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @role.sub_command()
    async def set_role(self, inter: ApplicationCommandInteraction) -> None:
        pass


def setup(bot: Robomania):
    bot.add_cog(Roles(bot))
