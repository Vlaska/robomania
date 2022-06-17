from __future__ import annotations

import datetime
import io
from pathlib import Path
from typing import Any, Awaitable, Generator, cast
from urllib.parse import urlparse

import aiohttp
import disnake
import pymongo
from disnake.ext import commands, tasks  # type: ignore[attr-defined]
from facebook_scraper import get_posts
from pymongo.database import Database

from . import utils

MAX_IMAGES_PER_MESSAGE = 10
MAX_TOTAL_SIZE_OF_IMAGES = 8 * 1024


class Announcements(commands.Cog):
    fields_to_keep = [
        'timestamp',
        'post_text',
        'post_id',
        'images',
        'post_url',
    ]
    fanpage_name = 'domeq.krk'
    target_channels_ids = [
        958823316850880515,  # Trash - general
    ]
    last_checked = datetime.datetime(1, 1, 1)
    target_channels: list[disnake.TextChannel]
    DOWNLOAD_PAGE_LIMIT = 4

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_for_announcements.start()

    async def create_collections(self, db: Database) -> None:
        posts = db.posts
        await cast(
            Awaitable,
            posts.create_index([('timestamp', pymongo.DESCENDING)])
        )

    def cog_unload(self) -> None:
        self.check_for_announcements.cancel()

    # TODO
    def check_enough_time_from_last_check(self) -> bool:
        pass

    @tasks.loop(seconds=10)  # TODO
    async def check_for_announcements(self) -> None:
        posts = await self.download_facebook_posts()
        # posts.sort(key=lambda x: x['timestamp'])
        new_posts = await self.get_only_new_posts(posts)
        for post in new_posts[::-1]:
            await self.send_announcements(post)

        await self.save_posts(new_posts)

    async def save_posts(self, posts: list[dict[str, Any]]) -> None:
        col = utils.get_db('robomania')

        await cast(
            Awaitable,
            col.posts.insert_many(posts, ordered=False)
        )

    async def get_latest_post_timestamp(self) -> int:
        db = utils.get_db('robomania')
        col = db.posts

        try:
            latest_post = await cast(Awaitable, col.aggregate([
                {'$sort': {'timestamp': -1}},
                {'$limit': 1},
                {'$project': {'_id': 0, 'timestamp': 1}}
            ]).next())
        except StopAsyncIteration:
            timestamp = 0
        else:
            timestamp = latest_post['timestamp']

        return timestamp

    async def get_only_new_posts(
        self,
        posts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        latest_timestamp = await self.get_latest_post_timestamp()

        return list(filter(lambda x: x['timestamp'] > latest_timestamp, posts))

    @check_for_announcements.before_loop
    async def init(self) -> None:
        client = utils.get_client()

        await self.create_collection(client.robomania)

        print('Waiting...')

        await self.bot.wait_until_ready()
        self.target_channels = []
        for i in self.target_channels_ids:
            self.target_channels.append(self.bot.get_channel(i))

    async def download_facebook_posts(self) -> list[dict[str, Any]]:
        return list(
            get_posts(self.fanpage_name, page_limit=self.DOWNLOAD_PAGE_LIMIT)
        )

    @classmethod
    def filter_fields(cls, post: dict[str, Any]) -> dict[str, Any]:
        return {
            k: post[k] for k in cls.fields_to_keep
        }

    async def _send_announcements(
        self,
        text: str = None,
        imgs: list[disnake.File] = None
    ) -> None:
        for channel in self.target_channels:
            await channel.send(
                text,
                files=cast(list[disnake.File], imgs)
            )

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

        return out

    # TODO
    def split_text(self, text: str, char_limit: int = 2000) -> list[str]:
        pass

    def prepare_images(
        self,
        images: list[tuple[io.BytesIO, str]]
    ) -> Generator[list[disnake.File], None, list[disnake.File]]:
        current_image_group: list[disnake.File] = []
        current_total_size = 0

        try:
            while True:
                image_data, image_name = images.pop(0)
                image_size = image_data.getbuffer().nbytes

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

        return current_image_group

    def format_announcements_date(self, timestamp: int) -> str:
        return f'Post zamieszczono: <t:{timestamp}:F>\n'

    def format_posts_url(self, url: str) -> str:
        return f'\nOryginał: {url}'

    def format_announcement_text(
        self,
        text: str,
        timestamp: int,
        post_url: str
    ) -> list[str]:
        # TODO: Split too long text into parts
        formatted_timestamp = self.format_announcements_date(timestamp)
        formatted_url = self.format_posts_url(post_url)

        total_length = sum(
            map(len, (formatted_timestamp, formatted_url, text))
        )

        out = []

        if total_length > 2000:
            space_required = total_length - len(text) + len('…')
            text = f'{text[:-space_required].strip()}…'

        out.append(
            f'{formatted_timestamp}{text}{formatted_url}'
        )

        return out

    async def send_announcements(self, post: dict[str, Any]) -> None:
        text: str = post['post_text']
        image_urls: list[str] = post['images']
        timestamp: int = post['timestamp']
        post_url: str = post['post_url']

        formatted_text = self.format_announcement_text(
            text, timestamp, post_url
        )

        for i in formatted_text[:-1]:
            await self._send_announcements(i)

        image_data = await self.download_images(image_urls)
        images = self.prepare_images(image_data)

        await self._send_announcements(
            formatted_text[-1],
            next(images)
        )

        for imgs in images:
            await self._send_announcements(None, imgs)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Announcements(bot))
