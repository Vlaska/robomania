import logging
import re
from functools import partial
from textwrap import TextWrapper
from typing import Protocol

import disnake
from disnake import Embed, File
from disnake.interactions import ApplicationCommandInteraction
from typing_extensions import Self

from robomania.types.image import Image
from robomania.utils.pipe import Pipe

MAX_CHARACTERS_PER_POST = 2000
MAX_CHARACTERS_FOR_EMBED = 4096

space_regex = re.compile(" +")
space_before_punctuation = re.compile(" (?=[.,?!–—-])")
three_dots = re.compile("\\.{3}")


logger = logging.getLogger("robomania.message")


class Message:
    text: str
    images: list[File]
    embeds: list[Embed]
    suppress_embeds: bool = False

    @property
    def has_files(self) -> bool:
        return len(self.images) != 0

    def __init__(
        self,
        text: str = "",
        images: list[Image] | None = None,
        embeds: list[Embed] | None = None,
    ) -> None:
        self.text = text
        # if images and embeds and any(self.does_embed_have_files(i) for i in embeds):
        #     raise ValueError("Cannot pass both images and embeds with files to send.")

        self.images = [i.file for i in (images or [])]
        self.embeds = embeds or []

    @staticmethod
    def does_embed_have_files(embed: Embed) -> bool:
        return len(embed._files) != 0

    @property
    def is_empty(self) -> bool:
        return not bool(self.text or self.images or self.embeds)

    async def send(
        self,
        message_target: ApplicationCommandInteraction | disnake.abc.Messageable,
    ) -> None:
        if self.is_empty:
            return

        try:
            await self.__send(message_target)
        except disnake.HTTPException as e:
            logger.error("Failed to message, retrying", exc_info=e)
        except ValueError as e:
            logger.error("Message too big, retrying", exc_info=e)
        else:
            return

        try:
            await self.__send(message_target, True)
        except Exception as e:
            logger.error("Failed to send message", exc_info=e)

    async def __send(
        self,
        message_target: ApplicationCommandInteraction | disnake.abc.Messageable,
        separate_embeds: bool = False,
    ) -> None:
        if isinstance(message_target, ApplicationCommandInteraction):
            send = message_target.response.send_message
        else:
            send = message_target.send  # type: ignore

        await send(
            self.text or None,
            embeds=self.embeds if not separate_embeds else [],
            files=self.images,
            suppress_embeds=self.suppress_embeds,
        )
        if separate_embeds:
            await send(embeds=self.embeds)


class TextProcessorProtocol(Protocol):
    def __call__(self, text: str) -> list[str]:
        pass


class TextProcessor(TextProcessorProtocol):
    wrapper = TextWrapper(
        MAX_CHARACTERS_PER_POST, expand_tabs=False, replace_whitespace=False
    )

    text_processing_pipeline: Pipe[str] = (
        Pipe()
        | str.strip
        | partial(space_regex.sub, " ")
        | partial(space_before_punctuation.sub, "")
        | partial(three_dots.sub, "…")
    )

    @classmethod
    def _wrap_text(cls, text: str) -> list[str]:
        if len(text) <= MAX_CHARACTERS_PER_POST:
            return [text]

        return cls.wrapper.wrap(text)

    def __call__(self, text: str) -> list[str]:
        return self._wrap_text(self.text_processing_pipeline(text))


class EmbedTextProcessor(TextProcessor):
    wrapper = TextWrapper(
        MAX_CHARACTERS_FOR_EMBED, expand_tabs=False, replace_whitespace=False
    )


class MessageBuilder:
    messages: list[Message]

    def __init__(self, text_processor: TextProcessorProtocol | None = None) -> None:
        self.text_processor = text_processor or TextProcessor()
        self.messages = []
        self.new_message()

    def process_text(self, text: str) -> list[str]:
        return self.text_processor(text)

    def text_with_images_message(self, text: str, images: list[Image]) -> Self:
        i: object
        *split_text, last_text = self.process_text(text)

        for i in split_text:
            self.add_text(i).suppress_embed(True).new_message()

        self.add_text(last_text).suppress_embed(True)

        if images:
            image_batcher = Image.prepare_images(images)

            for i in image_batcher:
                self.add_images(i).suppress_embed(True).new_message()

        return self

    def message_with_embeds_and_images(
        self, embeds: list[Embed], images: list[Image]
    ) -> Self:
        self.add_embeds(embeds).new_message()

        if images:
            image_batcher = Image.prepare_images(images)

            for i in image_batcher:
                self.add_images(i).new_message()

        return self

    def new_message(self) -> Self:
        self.current_message = Message()
        self.messages.append(self.current_message)
        return self

    def add_text(self, text: str) -> Self:
        self.current_message.text = text
        return self

    def add_images(self, images: list[File]) -> Self:
        if len(images) > 10:
            raise ValueError("Max 10 images allowed")

        self.current_message.images = images
        return self

    def add_embeds(self, embeds: list[Embed]) -> Self:
        if len(embeds) > 10:
            raise ValueError("Max 10 embeds allowed")

        self.current_message.embeds = embeds
        return self

    def add_embed(self, embed: Embed) -> Self:
        if len(self.current_message.embeds) > 9:
            raise ValueError("Max 10 embeds allowed")

        self.current_message.embeds.append(embed)
        return self

    async def send(
        self, message_target: ApplicationCommandInteraction | disnake.abc.Messageable
    ) -> None:
        for i in self.messages:
            await i.send(message_target)

    def suppress_embed(self, value: bool) -> Self:
        self.current_message.suppress_embeds = value
        return self
