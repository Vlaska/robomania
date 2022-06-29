from __future__ import annotations

import asyncio
import datetime
import io
import logging
import os
import re
from functools import partial
from itertools import product
from pathlib import Path
from textwrap import TextWrapper
from typing import Any, Awaitable, Generator, Iterator, cast
from urllib.parse import urlparse

import aiohttp
import disnake
import pymongo
from disnake.ext import commands, tasks  # type: ignore[attr-defined]
from facebook_scraper import get_posts
from PIL import Image
from pymongo.database import Database

from robomania.bot import DEBUG, Robomania

MAX_IMAGES_PER_MESSAGE = 10
MAX_TOTAL_SIZE_OF_IMAGES = 8 * 1024 * 1024
MAX_CHARACTERS_PER_POST = 2000


logger = logging.getLogger('robomania.announcements')

space_regex = re.compile(' +')

Post = dict[str, Any]
Posts = list[Post]


class PostDownloader:
    DONE = object()
    FACEBOOK_COOKIES_PATH = os.getenv('FACEBOOK_COOKIES_PATH')

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        lazy_posts: Iterator[Post]
    ) -> None:
        self._lazy_posts = lazy_posts
        self.loop = loop

    def __aiter__(self):
        return self

    async def __anext__(self) -> Post:
        out: Post | object = await self.loop.run_in_executor(
            None,
            next,
            self._lazy_posts,
            self.DONE
        )

        if out is self.DONE:
            raise StopAsyncIteration

        return cast(Post, out)

    async def get_all(self) -> Posts:
        out = []

        async for i in self:
            out.append(i)

        return out

    @classmethod
    async def new(
        cls,
        loop: asyncio.AbstractEventLoop,
        fanpage: str,
        pages: int
    ) -> PostDownloader:
        lazy_posts = await loop.run_in_executor(
            None,
            partial(
                get_posts,
                fanpage,
                page_limit=pages,
                cookies=cls.FACEBOOK_COOKIES_PATH
            )
        )
        return cls(loop, lazy_posts)


class Announcements(commands.Cog):
    fields_to_keep = [
        'timestamp',
        'post_text',
        'post_id',
        'images',
        'post_url',
    ]
    fanpage_name = 'domeq.krk'

    target_channel_id = 958823316850880515  # Trash - general

    last_checked = datetime.datetime(1, 1, 1)
    target_channel: disnake.TextChannel
    DOWNLOAD_PAGE_LIMIT = 3
    MIN_DELAY_BETWEEN_CHECKS = datetime.timedelta(minutes=25)
    _DISABLE_ANNOUNCEMENTS_LOOP = False
    DOWNSAMPLE_IMAGE_RESOLUTION_BY = [3 / 4, 1 / 2, 1 / 4, 1 / 8, 1 / 16]

    wrapper = TextWrapper(
        MAX_CHARACTERS_PER_POST,
        expand_tabs=False,
        replace_whitespace=False
    )
    checking_interval_hours = (7, 21)
    check_every_minutes = (0, 30)

    def __init__(self, bot: Robomania):
        self.bot = bot
        self.check_lock = asyncio.Lock()
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
                posts = await self.get_only_new_posts(posts)
                posts = self.filter_out_only_event_posts(posts)

                if not posts:
                    logger.info('No new posts found')
                    return

                logger.info(f'Sending {len(posts)} announcements')
                for post in posts:
                    await self.send_announcements(post)

                await self.save_posts(posts)
            except Exception:
                logger.exception('')

    @check_for_announcements.before_loop
    async def init(self) -> None:
        logger.info('Waiting for connection to discord...')
        await self.bot.wait_until_ready()

        client = self.bot.client
        await self.create_collections(client.robomania)

        self.target_channel = self.bot.get_channel(self.target_channel_id)
        await self._check_for_announcements()

    async def send_announcements(self, post: Post) -> None:
        text: str = post['post_text']
        image_urls: list[str] = post['images']
        timestamp: int = post['timestamp']
        post_url: str = post['post_url']

        formatted_text = self.format_announcement_text(
            text, timestamp, post_url
        )

        for i in formatted_text[:-1]:
            await self._send_announcements(i)

        if not image_urls:
            await self._send_announcements(formatted_text[-1])
            return

        image_data = await self.download_images(image_urls)
        images = self.prepare_images(image_data)

        await self._send_announcements(
            formatted_text[-1],
            next(images)
        )

        for imgs in images:
            await self._send_announcements(None, imgs)

    async def _send_announcements(
        self,
        text: str = None,
        imgs: list[disnake.File] = None
    ) -> None:
        await self.target_channel.send(
            text,
            files=cast(list[disnake.File], imgs),
            suppress_embeds=True,
        )

    def format_announcement_text(
        self,
        text: str,
        timestamp: int,
        post_url: str,
    ) -> list[str]:
        formatted_timestamp = self.format_announcements_date(timestamp)
        formatted_url = self.format_posts_url(post_url)

        text = self.clean_whitespaces_in_text(text)
        cleaned_text = disnake.utils.escape_markdown(text)

        out = self.split_text(
            f'{formatted_timestamp}{cleaned_text}{formatted_url}'
        )

        return out

    def format_announcements_date(self, timestamp: int) -> str:
        return f'**Post zamieszczono: <t:{timestamp}:F>**\n'

    def format_posts_url(self, url: str) -> str:
        return f'\nOryginał: {url}'

    def split_text(
        self,
        text: str,
        char_limit: int = 2000,
    ) -> list[str]:
        if len(text) <= char_limit:
            return [text]

        return self.wrapper.wrap(text)

    @staticmethod
    def clean_whitespaces_in_text(text: str) -> str:
        return space_regex.sub(' ', text)

    async def download_facebook_posts(self) -> Posts:
        loop = self.bot.loop
        logger.debug('Downloading facebook posts')

        post_iter = await PostDownloader.new(
            loop,
            self.fanpage_name,
            self.DOWNLOAD_PAGE_LIMIT
        )
        return await post_iter.get_all()

    async def save_posts(self, posts: Posts) -> None:
        db = self.bot.get_db('robomania')

        await cast(
            Awaitable,
            db.posts.insert_many(posts, ordered=False)
        )

    async def get_only_new_posts(self, posts: Posts) -> Posts:
        latest_timestamp = await self.get_latest_post_timestamp()
        logger.debug('Filtering out old posts')

        return sorted(
            filter(
                lambda x: x['timestamp'] > latest_timestamp,
                posts),
            key=lambda x: x['timestamp'])

    @staticmethod
    def _post_contains_event(post: Post) -> bool:
        return any(i['name'] == 'event' for i in post['with'])

    def filter_out_only_event_posts(self, posts: Posts) -> Posts:
        def condition(x: Post) -> bool:
            return not (
                not x['post_text'] and
                self._post_contains_event(x)
            )

        return list(filter(condition, posts))

    @classmethod
    def filter_fields(cls, post: Post) -> Post:
        return {
            k: post[k] for k in cls.fields_to_keep
        }

    async def download_images(
        self,
        images: list[str]
    ) -> list[tuple[io.BytesIO, str]]:
        out = []
        async with aiohttp.ClientSession() as session:
            for url in images:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        print('problem with image download')

                    data = io.BytesIO(await resp.read())
                    image_path = Path(urlparse(url).path)
                    out.append((data, image_path.name))

        logger.debug(f'Downloaded {len(out)} images')
        return out

    def prepare_images(
        self,
        images: list[tuple[io.BytesIO, str]]
    ) -> Generator[list[disnake.File], None, None]:
        current_image_group: list[disnake.File] = []
        current_total_size = 0

        try:
            while True:
                image_data, image_name = images.pop(0)
                image_size = image_data.getbuffer().nbytes

                if image_size > MAX_TOTAL_SIZE_OF_IMAGES:
                    try:
                        image_data = self.reduce_image_size(image_data)
                        image_size = image_data.getbuffer().nbytes
                    except ValueError:
                        continue

                if (
                    len(current_image_group) + 1 > MAX_IMAGES_PER_MESSAGE or
                    image_size + current_total_size > MAX_TOTAL_SIZE_OF_IMAGES
                ):
                    yield current_image_group

                    current_image_group = []
                    current_total_size = 0

                current_total_size += image_size
                current_image_group.append(
                    disnake.File(image_data, image_name)
                )
        except IndexError:
            pass

        yield current_image_group

    def reduce_image_size(self, image: io.BytesIO) -> io.BytesIO:
        logger.warning(
            'Image too big to be send, convertingO to jpg'
        )
        image = self.change_image_format(image)
        image_size = image.getbuffer().nbytes

        if image_size > MAX_TOTAL_SIZE_OF_IMAGES:
            for i in self.DOWNSAMPLE_IMAGE_RESOLUTION_BY:
                _image = self.reduce_image_resolution(image, i)

                if _image.getbuffer().nbytes < MAX_TOTAL_SIZE_OF_IMAGES:
                    image = _image
                    break
            else:
                logger.error('Image size still too big, skipping')
                raise ValueError('Image size still too big')

        return image

    def reduce_image_resolution(
        self,
        image: io.BytesIO,
        factor: float
    ) -> io.BytesIO:
        out = io.BytesIO()
        img = Image.open(image)
        old_x, old_y = img.size
        new_size = (int(old_x * factor), int(old_y * factor))
        resized_img = img.resize(new_size)
        resized_img.save(out, 'jpeg')
        return out

    def change_image_format(self, image: io.BytesIO) -> io.BytesIO:
        out = io.BytesIO()
        img = Image.open(image)
        img.convert('RGB').save(out, 'jpeg')
        return out

    def enough_time_from_last_check(self) -> bool:
        current_time = datetime.datetime.now()
        time_since_last_check = \
            current_time - self.bot.announcements_last_checked

        return time_since_last_check > self.MIN_DELAY_BETWEEN_CHECKS

    async def get_latest_post_timestamp(self) -> int:
        db = self.bot.get_db('robomania')
        col = db.posts

        latest_post = await cast(Awaitable, col.aggregate([  # type: ignore
            {'$sort': {'timestamp': -1}},
            {'$limit': 1},
            {'$project': {'_id': 0, 'timestamp': 1}}
        ]).to_list(1))

        if latest_post:
            timestamp = latest_post[0]['timestamp']
        else:
            logger.warning('No posts in database, using 0.')
            timestamp = 0

        return timestamp

    def cog_unload(self) -> None:
        self.check_for_announcements.stop()

    async def create_collections(self, db: Database) -> None:
        posts = db.posts
        await cast(
            Awaitable,
            posts.create_index([('timestamp', pymongo.DESCENDING)])
        )

    if DEBUG:
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
