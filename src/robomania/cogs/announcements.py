# type: ignore[name-defined]
from __future__ import annotations

import asyncio
import datetime
import logging

import disnake
import httpx  # type: ignore[attr-defined]
from disnake.ext import commands, tasks

from robomania import config
from robomania.bot import Robomania
from robomania.models.facebook_post import FacebookPosts, FacebookPostScraped
from robomania.types.announcement_post import AnnouncementPost

logger = logging.getLogger("robomania.cogs.announcements")


class Announcements(commands.Cog):
    target_channel: disnake.TextChannel
    MIN_DELAY_BETWEEN_CHECKS = datetime.timedelta(minutes=25)
    _DISABLE_ANNOUNCEMENTS_LOOP = False

    checking_interval_hours = (0, 23)
    check_every_minutes = (10, 40)

    def __init__(self, bot: Robomania):
        self.bot = bot
        self.check_lock = asyncio.Lock()

        self.target_channel_id = config.settings.announcements_target_channel

        if not self._DISABLE_ANNOUNCEMENTS_LOOP:
            self.check_for_announcements.start()

    # @tasks.loop(time=[
    #     datetime.time(hour=h, minute=m)
    #     for h, m in product(
    #         range(*checking_interval_hours),
    #         check_every_minutes
    #     )
    # ])
    @tasks.loop(minutes=5)
    async def check_for_announcements(self) -> None:
        # if not self.enough_time_from_last_check():
        #     logger.info('Not enough time passed since last check.')
        #     return

        logger.info("Checking for announcements.")
        await self._check_for_announcements()

    @check_for_announcements.before_loop
    async def init(self) -> None:
        logger.info("Waiting for connection to discord...")
        await self.bot.wait_until_ready()

        self.target_channel = self.bot.get_channel(self.target_channel_id)
        await self._check_for_announcements()

    async def _check_for_announcements(self) -> None:
        if self.check_lock.locked():
            logger.info("Trying to check for announcements, while check is" " already running")
            return

        async with self.check_lock:
            try:
                self.bot.announcements_last_checked = datetime.datetime.now()

                posts = await self.download_facebook_posts()

                if not posts:
                    logger.info("No new posts found")
                    return

                await self.send_annoucements(posts)

            except Exception as e:
                logger.exception(str(e))

    async def send_annoucements(self, posts: FacebookPosts) -> None:
        logger.info(f"Sending {len(posts)} announcements")
        for post in posts:
            # await self.send_announcements(post)
            announcement = AnnouncementPost.new(post)
            await announcement.send(self.target_channel)

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.bot.settings.scraping_service_url}posts/posted", json={"ids": [i.post_id for i in posts]}
            )

    async def download_facebook_posts(self) -> FacebookPosts:
        logger.debug("Downloading facebook posts")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.bot.settings.scraping_service_url}posts/unposted")
        try:
            raw_posts = response.json().get("data", [])
        except Exception:
            raw_posts = []
        logger.info(f"Got {len(raw_posts)} posts")

        return [FacebookPostScraped(**x) for x in raw_posts]

    def cog_unload(self) -> None:
        self.check_for_announcements.stop()

    if config.settings.debug:

        @commands.slash_command(name="check")
        async def command_posts(
            self,
            inter: disnake.ApplicationCommandInteraction,
        ) -> None:
            await inter.send("Ok", delete_after=5)
            await self._check_for_announcements()


def setup(bot: Robomania) -> None:
    bot.add_cog(Announcements(bot))
