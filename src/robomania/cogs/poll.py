# type: ignore[name-defined]
# flake8: noqa: W504
from __future__ import annotations

import enum
import logging
import random
from typing import TYPE_CHECKING

from disnake import (AllowedMentions, ApplicationCommandInteraction, Locale,
                     Localised, OptionChoice)
from disnake.ext import commands

if TYPE_CHECKING:
    from disnake import Role

    from robomania.bot import Robomania


logger = logging.getLogger('robomania.cogs.poll')


class DomeqPronounsRoles(enum.IntEnum):
    ON = 954064720351084587
    ONA = 954064729821823007
    ONO = 954064827595239505
    WILDCARD = 954064883438190713
    NEUTRAL = 954064945400668170

    def get_translation_key(self) -> str:
        match self:
            case (
                DomeqPronounsRoles.ON |
                DomeqPronounsRoles.ONA |
                DomeqPronounsRoles.ONO
            ):
                return f'POLL_CREATE_CREATED_BY_{self.name}'
            case DomeqPronounsRoles.WILDCARD:
                pick = random.choice([
                    DomeqPronounsRoles.ON,
                    DomeqPronounsRoles.ONA,
                    DomeqPronounsRoles.ONO,
                    DomeqPronounsRoles.NEUTRAL,
                ])
                return pick.get_translation_key()
            case DomeqPronounsRoles.NEUTRAL:
                return ''


emotes = {
    'numbers': [
        '1️⃣',
        '2️⃣',
        '3️⃣',
        '4️⃣',
        '5️⃣',
        '6️⃣',
        '7️⃣',
        '8️⃣',
        '9️⃣',
        '🔟'
    ],
    'hearts': [
        '❤️',
        '💚',
        '💙',
        '🧡',
        '💜',
        '❤️‍🩹',
        '💞',
        '🤍',
        '💛',
        '🫀'
    ],
}


class Poll(commands.Cog):
    def __init__(self, bot: Robomania):
        self.bot = bot

    @commands.slash_command()
    async def poll(
        self,
        inter: ApplicationCommandInteraction,
        question: str,
        options: str,
        theme: str = commands.Param(default='hearts', choices=[
            OptionChoice(
                Localised('numbers', key='POLL_OPTION_NUMBERS'),
                'numbers'
            ),
            OptionChoice(
                Localised('hearts', key='POLL_OPTION_HEARTS'),
                'hearts'
            ),
        ])
    ):
        """Create a poll  {{ POLL_CREATE }}

        Parameters
        ----------
        inter : ApplicationCommandInteraction
            Command interaction
        question : str
            Question for a poll
            {{ POLL_QUESTION }}
        options : str
            Options for poll separated with '|'
            {{ POLL_OPTIONS }}
        theme : str
            Style of reactions for options
            {{ POLL_REACTIONS }}
        """
        logger.info(
            f'Requested new poll: {question=}, {options=}, {theme=}'
        )
        if isinstance(theme, enum.Enum):
            theme = theme.value

        selected_theme = emotes[theme]
        separated_options = options.split('|')
        with self.bot.localize(inter.guild_locale or inter.locale) as tr:
            if len(separated_options) > 10:
                logger.info('Failed to create poll, too many options')
                await inter.send(
                    tr('POLL_TOO_MANY_OPTIONS'),
                    ephemeral=True
                )
                return

            message_arguments = {
                'user': inter.user.mention,
                'question': question
            }

            if inter.guild_id == 688337005402128386:
                user_roles = inter.user.roles
                roles_in_domeq = list(DomeqPronounsRoles)
                pronouns: list[Role] = [
                    i for i in user_roles if i.id in roles_in_domeq
                ]
                if pronouns:
                    selected_pronouns = DomeqPronounsRoles(pronouns[-1].id)
                    t = selected_pronouns.get_translation_key()
                    if not t:
                        message_template_key = 'POLL_CREATE_MESSAGE_TEMPLATE'
                    else:
                        message_template_key = 'POLL_CREATE_MESSAGE_WITH_PRONOUNS_TEMPLATE'  # noqa: E501
                        message_arguments['created'] = self.bot.tr(
                            t, Locale.pl
                        )

                    message_template: str = self.bot.tr(
                        message_template_key,
                        Locale.pl
                    )
            else:
                message_template: str = tr('POLL_CREATE_MESSAGE_TEMPLATE')

            message = message_template.format_map(message_arguments)

            message += '\n---\n' + '\n'.join(
                f'{emote}: {option.strip()}' for emote, option in zip(
                    selected_theme, separated_options
                ))

            await inter.send(
                message,
                suppress_embeds=True,
                allowed_mentions=AllowedMentions(users=False)
            )
            response = await inter.original_response()
            for emote in selected_theme[:len(separated_options)]:
                await response.add_reaction(emote)


def setup(bot: Robomania):
    bot.add_cog(Poll(bot))
