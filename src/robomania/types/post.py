from __future__ import annotations

import re
from functools import partial
from textwrap import TextWrapper
from typing import Any, Generator, Generic, Iterable, TypeVar, cast

import disnake

from robomania.types.image import Image
from robomania.utils.pipe import Pipe

MAX_CHARACTERS_PER_POST = 2000

space_regex = re.compile(' +')
space_before_punctuation = re.compile(' (?=[.,?!–—-])')
three_dots = re.compile('\\.{3}')

ImageType = TypeVar('ImageType', Image, str, )


class Post(Generic[ImageType]):
    _images: list[ImageType] | None = None
    _text: str
    wrapped_text: list[str]

    wrapper = TextWrapper(
        MAX_CHARACTERS_PER_POST,
        expand_tabs=False,
        replace_whitespace=False
    )

    text_processing_pipeline = (
        Pipe()
        | str.strip
        | partial(space_regex.sub, ' ')
        | partial(space_before_punctuation.sub, '')
        | partial(three_dots.sub, '…')
        | disnake.utils.escape_markdown
    )

    def __init__(
        self,
        text: str,
        images: Iterable[ImageType] = None
    ) -> None:
        self.text = text

        if images:
            self._images = list(images)

    def process_text(self, text: str) -> str:
        return self.text_processing_pipeline(text)

    def _wrap_text(self) -> list[str]:
        if len(self._text) <= MAX_CHARACTERS_PER_POST:
            return [self._text]

        return self.wrapper.wrap(self._text)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = self.process_text(value)
        self.wrapped_text = self._wrap_text()

    @staticmethod
    async def _send(
        channel: disnake.TextChannel,
        text: str = None,
        images: list[disnake.File] = None,
        kwargs: dict[str, Any] = {}
    ) -> None:
        await channel.send(
            text,
            files=cast(list[disnake.File], images),
            **kwargs
        )

    @staticmethod
    async def _get_images(images: list[ImageType]) -> list[Image]:
        if isinstance(images[0], Image):
            return cast(list[Image], images)

        return list(await Image.download_images(
            cast(list[str], images)
        ))

    async def _prepare_images(self) -> tuple[
        list[disnake.File] | None,
        Generator[list[disnake.File], None, None] | None
    ]:
        if self._images:
            images = await self._get_images(self._images)
            images_to_send = Image.prepare_images(
                images
            )
            first_images = next(images_to_send)
        else:
            images_to_send = None
            first_images = None

        return first_images, images_to_send

    async def send(self, target: disnake.TextChannel, **kwargs) -> None:
        i: object

        text_to_send = self.wrapped_text.copy()
        try:
            last_messages_text = text_to_send.pop()
        except IndexError:
            last_messages_text = None

        first_images, images_to_send = await self._prepare_images()

        for i in text_to_send:
            await self._send(target, i, kwargs=kwargs)

        await self._send(target, last_messages_text, first_images, kwargs)

        if images_to_send:
            for i in images_to_send:
                await self._send(target, None, i, kwargs)
