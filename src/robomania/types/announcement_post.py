from __future__ import annotations

import logging
from datetime import datetime

import disnake

from robomania import config
from robomania.models.facebook_post import FacebookPostScraped
from robomania.types.image import Image
from robomania.types.message import EmbedTextProcessor, MessageBuilder

logger = logging.getLogger("robomania.types")


class AnnouncementPost:
    def __init__(self, post: FacebookPostScraped) -> None:
        self.post = post
        self.subpost = post.subpost

    def format_text(
        self,
        text: str,
    ) -> str:
        return f"{self.announcements_date}{text}{self.post_url}"

    @property
    def announcements_date(self) -> str:
        return f"**Post zamieszczono: <t:{self.post.timestamp}:F>**\n"

    @property
    def post_url(self) -> str:
        return f"\nOryginał: {self.post.url}"

    @staticmethod
    def format_image_url(image_url: str) -> str:
        return f"{config.settings.scraping_service_url}posts/image/{image_url}"

    @classmethod
    def new(cls, post: FacebookPostScraped) -> AnnouncementPost:
        return cls(post)

    async def send_subpost(self, target: disnake.TextChannel) -> None:
        if not self.subpost:
            return

        text_processor = EmbedTextProcessor()
        first_embed_text, *rest_texts = text_processor(self.subpost.text)
        author = self.subpost.author
        timestamp = datetime.fromtimestamp(self.subpost.timestamp)
        images = await Image.download_images(
            [self.format_image_url(i) for i in self.subpost.images]
        )

        embeds: list[disnake.Embed] = []

        embed = disnake.Embed.from_dict(
            {
                "author": {"name": author},
                "color": 0xF4E152,
                "description": first_embed_text,
            }
        )

        embeds.append(embed)

        for i in rest_texts:
            embeds.append(disnake.Embed.from_dict({"description": i}))

        embeds[-1].timestamp = timestamp

        await MessageBuilder().message_with_embeds_and_images(embeds, images).send(
            target
        )

    async def send(self, target: disnake.TextChannel, **kwargs) -> None:
        logger.info(
            f"Sending post with id={self.post.post_id} and "
            f"{len(self.post.images)} images."
        )

        text = self.format_text(self.post.text)
        images = await Image.download_images(
            [self.format_image_url(i) for i in self.post.images]
        )

        await MessageBuilder().text_with_images_message(text, images).send(target)

        await self.send_subpost(target)
