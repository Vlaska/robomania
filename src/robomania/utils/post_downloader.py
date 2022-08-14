from __future__ import annotations

import asyncio
from functools import partial
from typing import Any, Iterator, cast

from facebook_scraper import get_posts

from robomania.config import Config

FBPost = dict[str, Any]
FBPosts = list[FBPost]


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
            raise StopAsyncIteration

        return cast(FBPost, out)

    async def get_all(self) -> FBPosts:
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
                cookies=Config.facebook_cookies_path,
            )
        )
        return cls(loop, lazy_posts)
