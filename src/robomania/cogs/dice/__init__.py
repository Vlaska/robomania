# type: ignore[name-defined]
from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from robomania.cogs.dice.grammar import parse
from robomania.utils.exceptions import DivByZeroWarning

if TYPE_CHECKING:
    from robomania.bot import Robomania

logger = logging.getLogger('robomania.cogs.dice')


class Dice(commands.Cog):
    def __init__(self, bot: Robomania) -> None:
        self.bot = bot

    @commands.slash_command()
    async def roll(
        self,
        inter: ApplicationCommandInteraction,
        dice: str = commands.Param(min_length=1),
        hide: bool = commands.Param(False)
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
        hide : :class: `bool`
            Dice roll result will be visible only to you.
            {{ DICE_HIDE_ROLL }}
        """
        error: str | None = None
        error_level: int = logging.INFO
        internal_div_by_0: bool = False

        with self.bot.localize(inter.locale) as tr:
            try:
                parsed_dice = parse(dice)
            except Exception:
                logger.warning(f'Incorrect dice query: {dice!r}')
                await inter.response.send_message(
                    tr('DICE_INCORRECT_EXPRESSION')
                )
                return

            try:
                with warnings.catch_warnings(record=True) as w:
                    evaluated_expression = parsed_dice.eval_to_list()
                    internal_div_by_0 = len(w) > 0 and any(
                        issubclass(i.category, DivByZeroWarning) for i in w)
            except ZeroDivisionError as e:
                message = str(e)
                error = tr('DIVISION_BY_ZERO')
            except ValueError as e:
                error, key, *_ = e.args
                message = tr(key, error)
            except Exception as e:
                error = str(e)
                message = tr('INTERNAL_ERROR')
                error_level = logging.ERROR
            else:
                message = '\n'.join(
                    f'`{dice}` -> `{result.finalize()}`'
                    for dice, result
                    in zip(parsed_dice.expressions, evaluated_expression)
                )
                if len(message) >= 1500:
                    message = tr('DICE_MESSAGE_TOO_LONG')
                elif internal_div_by_0:
                    message += f'\n\n*{tr("DICE_INTERNAL_DIV_BY_ZERO")}*'
            finally:
                await inter.send(message, ephemeral=hide)

        if error:
            logger.log(
                error_level,
                f'Roll expression: "{dice}"; Error: {error}'
            )


def setup(bot: Robomania) -> None:
    bot.add_cog(Dice(bot))
