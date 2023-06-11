from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from disnake import Embed
from disnake.ext import commands
from disnake.interactions.application_command import ApplicationCommandInteraction
from disnake.types.embed import Embed as EmbedData

from robomania.config import settings
from robomania.utils.assets import get_asset_url

if TYPE_CHECKING:
    from robomania.bot import Robomania


logger = logging.getLogger("robomania.cogs.info")
ZRZUTKA_URL = "https://zrzutka.pl/6eh5d2"


class Info(commands.Cog):
    def __init__(self, bot: Robomania):
        self.bot = bot

    @commands.slash_command()
    async def info(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """Display various informations  {{ DISPLAY_INFO }}"""

    async def send_embed(
        self, inter: ApplicationCommandInteraction, embed: EmbedData
    ) -> None:
        await inter.send(embed=Embed.from_dict(embed))

    @info.sub_command()
    async def fundraiser(self, inter: ApplicationCommandInteraction) -> None:
        """Display info regarding fundraiser supporting DOM EQ  {{ INFO_FUNDRAISER }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Zrzutka",
                "color": 0xE83E3E,
                "thumbnail": {"url": get_asset_url("zrzutka-icon.png", "icon")},
                "url": ZRZUTKA_URL,
                "description": (
                    "Hej. Jeżeli możesz, wesprzyj DOM EQ na oficalnej zrzutce."
                ),
                "fields": [{"name": "Zrzutka", "value": ZRZUTKA_URL}],
            },
        )

    @info.sub_command()
    async def legal_advice(self, inter: ApplicationCommandInteraction) -> None:
        """Display contact info to Fundations legal help  {{ LEGAL_ADVICE }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Pomoc prawna",
                "description": (
                    "Potrzebujesz pomocy prawnej? Skontaktuj się z "
                    "prawnikami fundacji."
                ),
                "color": 0x2F89DE,
                "fields": [
                    {"name": "Email", "value": "pomoc.prawna@znakirownosci.org.pl"}
                ],
            },
        )

    @info.sub_command()
    async def address(self, inter: ApplicationCommandInteraction) -> None:
        """Display address of DOM EQ and how to get there with public transport  \
        {{ DOMEQ_ADDRESS }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Jak dostać się do DOM EQ",
                "description": (
                    "DOM EQ znajduje się niedaleko Ronda Matecznego przy ul. Czyżówka "
                    "43 w domku jednorodzinnym. Do środka wchodzi się zieloną bramą, "
                    "nie trzeba pukać!"
                ),
                "color": 0xBA41D5,
                "fields": [
                    {"name": "Adres", "value": "ul.Czyżówka 43,\n30-526 Kraków"},
                    {
                        "name": "Google Maps",
                        "value": (
                            "https://www.google.com/maps/place/Czy%C5%BC%C3%B3wka+43,"
                            "+30-526+Krak%C3%B3w,+Poland/@50.035777,19.943018,17z/data="
                            "!4m6!3m5!1s0x47165b5f325388e5:0x645c3382760092d6!8m2!3d50."
                            "0357772!4d19.943018!16s%2Fg%2F11c1zl8yv_?hl=pl-PL"
                        ),
                    },
                    {
                        "name": "Komunikacja miejska",
                        "value": (
                            "Do DOM EQ można łatwo dostać się komunikacją miejską. "
                            "Wystarczy złapać coś, co jedzie na Rondo Matecznego.\n"
                            "Autobusy: 144, 164, 169, 173, 179, 301, 304, "
                            "469, 503, 608, 610\n"
                            "Tramwaje: 8, 10, 17, 19"
                        ),
                    },
                ],
            },
        )

    @info.sub_command()
    async def fanimani(self, inter: ApplicationCommandInteraction) -> None:
        """Display link to Fanimani, with which you can support DOM EQ  {{ FANIMANI }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Fanimani",
                "description": (
                    "Robisz zakupy? Pamiętaj o Fanimani, dzięki któremu "
                    "możemy uzyskać średnio 2,5% wartości z zakupów na DOM EQ!"
                ),
                "color": 0xFF294E,
                "url": "https://fanimani.pl/domeq/",
                "fields": [
                    {
                        "name": "Federacja Znaki Równości na Fanimani",
                        "value": "https://fanimani.pl/domeq/",
                        "inline": True,
                    },
                ],
            },
        )

    @info.sub_command()
    async def support(self, inter: ApplicationCommandInteraction) -> None:
        """Display info about how to support Signs of Equality Foundation \
            {{ SUPPORT_FOUNDATION }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Wsparcie",
                "description": (
                    "Chcesz nas wesprzeć? Możesz to zrobić na wiele sposobów"
                ),
                "color": 0x5ED2FE,
                "fields": [
                    {"name": "Fanimani", "value": "https://fanimani.pl/domeq/"},
                    {"name": "Zrzutka.pl", "value": ZRZUTKA_URL},
                    {
                        "name": "Przelew",
                        "value": (
                            "Tytuł przelewu: **Na cele statutowe**"
                            "Nr konta bankowego: 61 1140 2004 0000 3602 7836 7437"
                        ),
                    },
                ],
            },
        )

    @info.sub_command()
    async def contact(self, inter: ApplicationCommandInteraction) -> None:
        """Display contact information {{ FOUNDATION_CONTACT }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Kontakt",
                "description": "Chesz się z nami skontaktować?",
                "color": 0xC4FF39,
                "fields": [
                    {
                        "name": "Email Federacji Znaki Równości",
                        "value": "kontakt@znakirownosci.org.pl",
                    },
                    {
                        "name": "Krakowskie Centrum Równości DOM EQ",
                        "value": "domeq@znakirownosci.org.pl",
                    },
                    {
                        "name": "Zespół prawny",
                        "value": "pomoc.prawna@znakirownosci.org.pl",
                    },
                    {
                        "name": "Zespół psychologiczny",
                        "value": "wsparcie@znakirownosci.org.pl",
                    },
                ],
            },
        )

    @info.sub_command()
    async def why_was_marianna_late(self, inter: ApplicationCommandInteraction) -> None:
        """Wonder why Marianna is late? I can answer it for you  {{ WHY_MARIANNA_LATE }}

        Parameters
        ----------
        inter : :class:`ApplicationCommandInteraction`
            Command interaction
        """
        await self.send_embed(
            inter,
            {
                "title": "Czemu Marianna się spóźnia?",
                "color": 0xFF18F7,
                "image": {
                    "url": get_asset_url("139-kombinat.png", "image"),
                },
            },
        )

    if settings.debug:

        @commands.slash_command()
        async def invite(self, inter: ApplicationCommandInteraction) -> None:
            """Display invite link to this server  {{ SERVER_INVITE }}

            Parameters
            ----------
            inter : :class:`ApplicationCommandInteraction`
                Command interaction
            """

        @commands.slash_command()
        async def embed(self, inter: ApplicationCommandInteraction, code: str) -> None:
            await inter.send(embed=Embed.from_dict(json.loads(code)))


def setup(bot: Robomania):
    bot.add_cog(Info(bot))
