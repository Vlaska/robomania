from __future__ import annotations

from typing import cast

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from robomania.bot import Robomania
from robomania.config import Config
from robomania.types.picrew_model import PicrewModel


class Picrew(commands.Cog):
    target_channel: disnake.TextChannel

    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

        target_channel_id = Config.picrew_target_channel
        self.target_channel = cast(
            disnake.TextChannel,
            self.bot.get_channel(target_channel_id)
        )

    @commands.slash_command()
    async def picrew(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @picrew.sub_command()
    async def add_new_link(
        self,
        inter: ApplicationCommandInteraction,
        url: str,
    ) -> None:
        """
        Add a new Picrew link to post later. {{ ADD_PICREW }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        url : :class:`str`
            Picrew link, must be valid url {{ ADD_PICREW_URL }}
        """
        pass

    @picrew.sub_command()
    async def status(
        self,
        inter: ApplicationCommandInteraction,
    ) -> None:
        await inter.response.defer()

        db = self.bot.get_db('robomania')
        count = await PicrewModel.count_posted_and_not_posted(db)

        await inter.followup.send(
            f'Obecnie {count.not_posted} linków czeka na wysłanie. '
            f'Do tej pory zostało wysłanych {count.posted} linków.'
        )

    if Config.debug:
        @picrew.sub_command()
        async def post(self, inter: ApplicationCommandInteraction) -> None:
            pass


def setup(bot: Robomania) -> None:
    bot.add_cog(Picrew(bot))
