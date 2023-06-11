from __future__ import annotations

import logging
from typing import Iterable

import disnake

from robomania import config
from robomania.models.facebook_post import FacebookPostScraped
from robomania.types.image import Image

logger = logging.getLogger("robomania.types")


class AnnouncementPost:
    def __init__(
        self, post: FacebookPostScraped, images: Iterable[str] | None = None
    ) -> None:
        self.timestamp = post.timestamp
        self.url = post.url
        self.post_id = post.post_id
        self.subpost = post.subpost
        self.images = images

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
    async def new(cls, post: FacebookPostScraped) -> AnnouncementPost:
        images = await Image.download_images(
            [
                f"{config.settings.scraping_service_url}posts/image/{i}"
                for i in post.images
            ]
        )
        return cls(post, images)

    async def send(self, target: disnake.TextChannel, **kwargs) -> None:
        logger.info(
            f"Sending post with id={self.post_id} and {len(self._images)} images."
        )
