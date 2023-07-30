from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, cast

import disnake
import httpx
from disnake.ext import commands, tasks

from robomania import config
from robomania.models.facebook_post import FacebookPosts, FacebookPostScraped
from robomania.types.announcement_post import AnnouncementPost

if TYPE_CHECKING:
    from disnake.interactions.application_command import ApplicationCommandInteraction

    from robomania.bot import Robomania

logger = logging.getLogger("robomania.cogs.announcements")


class Announcements(commands.Cog):
    target_channel: disnake.TextChannel
    _DISABLE_ANNOUNCEMENTS_LOOP = False

    def __init__(self, bot: Robomania) -> None:
        self.bot = bot
        self.check_lock = asyncio.Lock()

        self.target_channel_id = config.settings.announcements_target_channel

        if not self._DISABLE_ANNOUNCEMENTS_LOOP:
            self.check_for_announcements.start()

    @tasks.loop(minutes=config.settings.time_betweent_announcements_check)
    async def check_for_announcements(self) -> None:
        logger.info("Checking for announcements.")
        await self._check_for_announcements()

    @check_for_announcements.before_loop
    async def init(self) -> None:
        logger.info("Waiting for connection to discord...")
        await self.bot.wait_until_ready()

        self.target_channel = cast(
            disnake.TextChannel, self.bot.get_channel(self.target_channel_id)
        )
        await self._check_for_announcements()

    async def _check_for_announcements(self) -> None:
        if self.check_lock.locked():
            logger.info(
                "Trying to check for announcements, while check is already running"
            )
            return

        async with self.check_lock:
            try:
                posts = await self.download_facebook_posts()

                if not posts:
                    return

                await self.send_annoucements(posts)

            except Exception as e:
                logger.exception(str(e))

    async def send_annoucements(self, posts: FacebookPosts) -> None:
        logger.info(f"Sending {len(posts)} announcements")
        for post in posts:
            announcement = AnnouncementPost.new(post)
            await announcement.send(self.target_channel)

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.bot.settings.scraping_service_url}posts/posted",
                json={"ids": [i.post_id for i in posts]},
            )

    async def download_facebook_posts(self) -> FacebookPosts:
        logger.debug("Downloading facebook posts")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot.settings.scraping_service_url}posts/unposted"
                )
        except httpx.RequestError as e:
            logger.warning("Couldn't reach scraper", exc_info=e)
            raw_posts = []
        else:
            try:
                raw_posts = response.json().get("data", [])
                logger.info(f"Got {len(raw_posts)} posts")
            except Exception:
                raw_posts = []

        return [FacebookPostScraped(**x) for x in raw_posts]

    def cog_unload(self) -> None:
        self.check_for_announcements.stop()

    if config.settings.debug:

        @commands.slash_command(name="check")
        async def command_posts(
            self,
            inter: ApplicationCommandInteraction,
        ) -> None:
            await inter.send("Ok", delete_after=5)
            await self._check_for_announcements()


def setup(bot: Robomania) -> None:
    bot.add_cog(Announcements(bot))
