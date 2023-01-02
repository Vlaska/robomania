# type: ignore[name-defined]
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from robomania.cogs.dice.grammar import parse

if TYPE_CHECKING:
    from robomania.bot import Robomania

logger = getLogger('robomania.cogs.dice')


class Dice(commands.Cog):
    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

    def parse_dice(self, dice: str) -> None:
        pass

    @commands.slash_command()
    async def roll(
        self,
        inter: ApplicationCommandInteraction,
        dice: str
    ) -> None:
        """Roll dice using any base. {{ DICE_ROLL }}

        Parameters
        ----------
        inter : :class: `ApplicationCommandInteraction`
            Command interaction
        dice : :class: `str`
            Dice to roll. Can be provided as one string.
            Ex.: "5d10 + 3 6d6 - 1" will result in two rolls.
            {{ DICE_TO_ROLL }}
        """
        try:
            parsed_dice = parse(dice)
        except Exception:
            logger.warning(f'Incorrect dice query: {dice!r}')
            await inter.response.send_message(
                'Nieprawidłowo sformatowane dane'
            )
            return

        results = (i.calc() for i in parsed_dice)
        await inter.response.send_message('\n'.join(
            f'{dice} = {result}'
            for dice, result
            in zip(parsed_dice, results)
        ))


def setup(bot: Robomania) -> None:
    bot.add_cog(Dice(bot))
