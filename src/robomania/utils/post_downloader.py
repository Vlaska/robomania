from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Any, Iterator, cast

from facebook_scraper import get_posts

from robomania.config import Config
from robomania.utils import preconfigure

FBPost = dict[str, Any]
FBPosts = list[FBPost]

logger = logging.getLogger('robomania.types')


@preconfigure
class PostDownloader:
    DONE = object()

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        lazy_posts: Iterator[FBPost]
    ) -> None:
        self._lazy_posts = lazy_posts
        self.loop = loop

    def __aiter__(self):
        return self

    async def __anext__(self) -> FBPost:
        out: FBPost | object = await self.loop.run_in_executor(
            None,
            next,
            self._lazy_posts,
            self.DONE
        )

        if out is self.DONE:
            logger.debug('Downloaded all posts')
            raise StopAsyncIteration

        logger.debug(f'Downloaded post {out["post_id"]}')  # type: ignore

        return cast(FBPost, out)

    async def get_all(self) -> FBPosts:
        out = []

        async for i in self:
            out.append(i)

        logger.info(f'Downloaded {len(out)} posts.')

        return out

    @classmethod
    async def new(
        cls,
        loop: asyncio.AbstractEventLoop,
        fanpage: str,
        pages: int
    ) -> PostDownloader:
        logger.debug(f'Download params: {fanpage=}, {pages=}')
        lazy_posts = await loop.run_in_executor(
            None,
            partial(
                get_posts,
                fanpage,
                page_limit=pages,
                cookies=Config.facebook_cookies_path,
            )
        )
        return cls(loop, lazy_posts)

    @classmethod
    async def download_posts(
        cls,
        fanpage: str,
        pages: int,
        loop: asyncio.AbstractEventLoop = None
    ) -> FBPosts:
        if not loop:
            loop = asyncio.get_event_loop()

        iterator = await cls.new(loop, fanpage, pages)

        return await iterator.get_all()

    @staticmethod
    def preconfigure() -> None:
        from facebook_scraper import _scraper
        locale = {'Accept-Language': 'en-US,en;q=0.5'}
        _scraper.session.headers.update(locale)
        _scraper.default_headers.update(locale)

        if Config.scraper_user_agent:
            _scraper.set_user_agent(Config.scraper_user_agent)
