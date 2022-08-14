# type: ignore[name-defined]
from __future__ import annotations

import asyncio
import datetime
import logging
from itertools import product
from typing import Awaitable, cast

import disnake
from disnake.ext import commands, tasks  # type: ignore[attr-defined]

from robomania.bot import Robomania
from robomania.config import Config
from robomania.types.announcement_post import AnnouncementPost
from robomania.types.facebook_post import FacebookPost, FacebookPosts
from robomania.utils.post_downloader import PostDownloader

logger = logging.getLogger('robomania.announcements')


class Announcements(commands.Cog):
    fanpage_name = 'domeq.krk'

    target_channel: disnake.TextChannel
    DOWNLOAD_PAGE_LIMIT = 3
    MIN_DELAY_BETWEEN_CHECKS = datetime.timedelta(minutes=25)
    _DISABLE_ANNOUNCEMENTS_LOOP = False

    checking_interval_hours = (7, 21)
    check_every_minutes = (0, 30)

    def __init__(self, bot: Robomania):
        self.bot = bot
        self.check_lock = asyncio.Lock()

        self.target_channel_id = self.bot.config.announcements_target_channel

        if not self._DISABLE_ANNOUNCEMENTS_LOOP:
            self.check_for_announcements.start()

    @tasks.loop(time=[
        datetime.time(hour=h, minute=m)
        for h, m in product(
            range(*checking_interval_hours),
            check_every_minutes
        )
    ])
    async def check_for_announcements(self) -> None:
        if not self.enough_time_from_last_check():
            logger.info('Not enough time passed since last check.')
            return

        logger.info('Checking for announcements.')
        await self._check_for_announcements()

    @check_for_announcements.before_loop
    async def init(self) -> None:
        logger.info('Waiting for connection to discord...')
        await self.bot.wait_until_ready()

        self.target_channel = self.bot.get_channel(self.target_channel_id)
        await self._check_for_announcements()

    async def _check_for_announcements(self) -> None:
        if self.check_lock.locked():
            logger.info(
                'Trying to check for announcements, while check is'
                ' already running'
            )
            return

        async with self.check_lock:
            try:
                self.bot.announcements_last_checked = datetime.datetime.now()

                posts = await self.download_facebook_posts()
                posts = await AnnouncementPost.get_only_new_posts(
                    self.bot.get_db('robomania'),
                    posts
                )
                posts = self.filter_out_only_event_posts(posts)

                if not posts:
                    logger.info('No new posts found')
                    return

                self.send_annoucements(posts)

            except Exception:
                logger.warning('')

    async def send_annoucements(self, posts: FacebookPosts) -> None:
        logger.info(f'Sending {len(posts)} announcements')
        for post in posts:
            # await self.send_announcements(post)
            announcement = AnnouncementPost.new(post)
            await announcement.send(self.target_channel)

        await FacebookPost.save(self.bot.get_db('robomania'), posts)

    async def download_facebook_posts(self) -> FacebookPosts:
        loop = self.bot.loop
        logger.debug('Downloading facebook posts')

        post_iter = await PostDownloader.new(
            loop,
            self.fanpage_name,
            self.DOWNLOAD_PAGE_LIMIT
        )
        raw_posts = await post_iter.get_all()

        return list(map(FacebookPost.from_raw, raw_posts))

    def enough_time_from_last_check(self) -> bool:
        current_time = datetime.datetime.now()
        time_since_last_check = \
            current_time - self.bot.announcements_last_checked

        return time_since_last_check > self.MIN_DELAY_BETWEEN_CHECKS

    def filter_out_only_event_posts(
        self,
        posts: FacebookPosts
    ) -> FacebookPosts:

        def condition(x: FacebookPost) -> bool:
            return not (not x.post_text and x.is_event)

        return list(filter(condition, posts))

    def cog_unload(self) -> None:
        self.check_for_announcements.stop()

    if Config.debug:
        @commands.slash_command(name='check')
        async def command_posts(
            self,
            inter: disnake.ApplicationCommandInteraction,
        ) -> None:
            await inter.send('Ok', delete_after=5)
            await self._check_for_announcements()

        @commands.slash_command(name='remove')
        async def remove_last_posts(
            self,
            inter: disnake.ApplicationCommandInteraction,
            num: int
        ) -> None:
            await inter.send('ok', delete_after=2)
            posts = self.bot.get_db('robomania').posts
            timestamp_raw = await cast(Awaitable, posts.aggregate([
                {'$sort': {'timestamp': -1}},
                {'$skip': max(num - 1, 0)},
                {'$limit': 1},
                {'$project': {'_id': 0, 'timestamp': 1}}
            ]).to_list(1))

            if not timestamp_raw:
                return

            timestamp = timestamp_raw[0]['timestamp']
            await cast(Awaitable, posts.delete_many({
                'timestamp': {'$gte': timestamp}
            }))


def setup(bot: Robomania) -> None:
    bot.add_cog(Announcements(bot))
