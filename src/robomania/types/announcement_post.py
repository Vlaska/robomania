from __future__ import annotations

import logging
from typing import Iterable

import disnake

from robomania import config
from robomania.models.facebook_post import FacebookPostScraped
from robomania.types.post import Post

logger = logging.getLogger("robomania.types")


class AnnouncementPost(Post[str]):
    def __init__(
        self, post: FacebookPostScraped, images: Iterable[str] | None = None
    ) -> None:
        self.timestamp = post.timestamp
        self.url = post.url
        self.post_id = post.post_id

        super().__init__(post.text, images)

    def process_text(self, text: str) -> str:
        return self.format_text(super().process_text(text))

    def format_text(
        self,
        text: str,
    ) -> str:
        return f"{self.announcements_date}{text}{self.post_url}"

    @property
    def announcements_date(self) -> str:
        return f"**Post zamieszczono: <t:{self.timestamp}:F>**\n"

    @property
    def post_url(self) -> str:
        return f"\nOryginał: {self.url}"

    @classmethod
    def new(cls, post: FacebookPostScraped) -> AnnouncementPost:
        images = [
            f"{config.settings.scraping_service_url}posts/image/{i}"
            for i in post.images
        ]
        return cls(post, images)

    async def send(self, target: disnake.TextChannel, **kwargs) -> None:
        logger.info(
            f"Sending post with id={self.post_id} and {len(self._images)} images."
        )
        await super().send(target, suppress_embeds=True, **kwargs)
