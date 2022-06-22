from __future__ import annotations

import datetime
import io
import logging
import math
import re
from pathlib import Path
from textwrap import TextWrapper
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
MAX_CHARACTERS_PER_POST = 2000


logger = logging.getLogger('disnake')

space_regex = re.compile(' +')


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
    MIN_DELAY_BETWEEN_CHECKS = datetime.timedelta(minutes=30)
    _DISABLE_ANNOUNCEMENTS_LOOP = False
    wrapper = TextWrapper(
        MAX_CHARACTERS_PER_POST,
        expand_tabs=False,
        replace_whitespace=False
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not self._DISABLE_ANNOUNCEMENTS_LOOP:
            self.check_for_announcements.start()

    async def create_collections(self, db: Database) -> None:
        posts = db.posts
        await cast(
            Awaitable,
            posts.create_index([('timestamp', pymongo.DESCENDING)])
        )

    def cog_unload(self) -> None:
        self.check_for_announcements.cancel()

    def enough_time_from_last_check(self) -> bool:
        current_time = datetime.datetime.now()
        time_since_last_check = current_time - utils.announcements_last_checked

        return time_since_last_check > self.MIN_DELAY_BETWEEN_CHECKS

    # TODO
    def in_allowed_time_range(self) -> bool:
        pass

    @tasks.loop(hours=1)  # TODO
    async def check_for_announcements(self) -> None:
        if not self.enough_time_from_last_check():
            return

        utils.announcements_last_checked = datetime.datetime.now()

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

    @staticmethod
    async def get_latest_post_timestamp() -> int:
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

        return sorted(
            filter(
                lambda x: x['timestamp'] > latest_timestamp,
                posts),
            key=lambda x: x['timestamp'])

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
        loop = self.bot.loop
        return list(
            await loop.run_in_executor(
                None,
                get_posts,
                self.fanpage_name,
                page_limit=self.DOWNLOAD_PAGE_LIMIT
            )
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

    def reduce_image_size(self, image: io.BytesIO) -> io.BytesIO:
        pass

    def split_very_long_word(
        self,
        word: str,
        char_limit: int
    ) -> list[str]:
        out = []
        char_per_line = char_limit - 1

        for i in range(len(word) // char_per_line):
            sub = f'{word[i * char_per_line:((i + 1) * char_per_line)]}-'
            out.append(sub)

        last = word[(i + 1) * char_per_line:]
        if not last:
            out[-1] = out[-1][:-1]
        elif len(last) == 1:
            out[-1] = f'{out[-1][:-1]}{last}'
        else:
            out.append(last)

        return out

    def _join_split_text(
        self,
        text: list[str],
        sep: str,
        end: str = ''
    ) -> str:
        return f'{sep.join(text)}{end}'.strip()

    def split_text(
        self,
        text: str,
        char_limit: int = 2000,
        sep: str = '\n'
    ) -> list[str]:
        if len(text) <= char_limit:
            return [text]

        # out: list[str] = []
        # # text_to_join: list[str] = []
        # sep_length = len(sep)
        # current_line = ''

        # current_text_length = 0

        # for line in text.split(sep):
        #     inner_separator = NEXT_LINE_SEPARATOR[sep]

        #     length = len(line)
        #     tmp = current_text_length + length + sep_length

        #     if length > char_limit:
        #         try:
        #             split_line = self.split_text(
        #                 line,
        #                 char_limit,
        #                 inner_separator
        #             )
        #         except KeyError:
        #             split_line = self.split_very_long_word(line, char_limit)
        #             inner_separator = ''

        #         # while current_text_length < char_limit and split_line:
        #         #     cur = split_line.pop(0)

        #         first_line = split_line[0] + inner_separator.strip()

        #         if current_text_length == 0:
        #             out.append(first_line)

        #             split_line.pop(0)
        #         elif current_text_length + \
        #                 len(first_line) + len(sep) <= char_limit:
        #             text_to_join.append(first_line)
        #             current_text_length += len(first_line)
        #             split_line.pop(0)

        #         if text_to_join:
        #             out.append(self._join_split_text(text_to_join, sep))

        #         out.extend(split_line[:-1])
        #         text_to_join = [split_line[-1]]
        #         current_text_length = len(split_line[-1])

        #         continue

        #     if tmp > char_limit:
        #         out.append(self._join_split_text(text_to_join, sep))
        #         text_to_join.clear()
        #         current_text_length = 0

        #     text_to_join.append(line)
        #     current_text_length += length

        # if text_to_join:
        #     out.append(self._join_split_text(text_to_join, sep))
            # new_length = current_text_length + sep_length + line
            # if new_length > char_limit:
            #     excess_chars

        # return out
        return self.wrapper.wrap(text)

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

    def format_announcements_date(self, timestamp: int) -> str:
        return f'Post zamieszczono: <t:{timestamp}:F>\n'

    def format_posts_url(self, url: str) -> str:
        return f'\nOryginał: {url}'

    @staticmethod
    def clean_whitespaces_in_text(text: str) -> str:
        return space_regex.sub(' ', text)

    def format_announcement_text(
        self,
        text: str,
        timestamp: int,
        post_url: str,
    ) -> list[str]:
        formatted_timestamp = self.format_announcements_date(timestamp)
        formatted_url = self.format_posts_url(post_url)

        text = self.clean_whitespaces_in_text(text)

        out = self.split_text(
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
