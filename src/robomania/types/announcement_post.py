from __future__ import annotations

import logging
from typing import Iterable

import disnake

from robomania.types.facebook_post import FacebookPost
from robomania.types.post import DiscordPost

logger = logging.getLogger('robomania')


class AnnouncementPost(DiscordPost[str]):
    def __init__(
        self,
        post: FacebookPost,
        images: Iterable[str] = None
    ) -> None:
        self.timestamp = post.timestamp
        self.url = post.post_url

        super().__init__(post.post_text, images)

    def process_text(self, text: str) -> str:
        return self.format_text(super().process_text(text))

    def format_text(
        self,
        text: str,
    ) -> str:
        return f'{self.announcements_date}{text}{self.post_url}'

    @property
    def announcements_date(self) -> str:
        return f'**Post zamieszczono: <t:{self.timestamp}:F>**\n'

    @property
    def post_url(self) -> str:
        return f'\nOryginał: {self.url}'

    @classmethod
    def new(cls, post: FacebookPost) -> AnnouncementPost:
        return cls(post, post.images)

    async def send(self, target: disnake.TextChannel, **kwargs) -> None:
        await super().send(target, suppress_embeds=True, **kwargs)
