import re
from functools import partial
from textwrap import TextWrapper
from typing import Iterable

import disnake

from robomania.types.image import Image
from robomania.utils.pipe import Pipe

MAX_CHARACTERS_PER_POST = 2000

space_regex = re.compile(" +")
space_before_punctuation = re.compile(" (?=[.,?!–—-])")
three_dots = re.compile("\\.{3}")


class Message:
    text: str
    images: list[Image]
    embeds: list["Embed"]

    @property
    def has_files(self) -> bool:
        return len(self.images) != 0

    def __init__(
        self,
        text: str = "",
        images: list[Image] | None = None,
        embeds: list["Embed"] | None = None,
    ) -> None:
        self.text = text
        if images and embeds and any(i.has_files for i in embeds):
            raise ValueError("Cannot pass both images and embeds with files to send.")

        self.images = images or []
        self.embeds = embeds or []


class Embed(disnake.Embed):
    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)

    @property
    def has_files(self) -> bool:
        return len(self._files) != 0


class Messages:
    images: Iterable[Image]
    _text: str
    processed_text: list[str]
    embeds: Iterable[Embed]

    wrapper = TextWrapper(
        MAX_CHARACTERS_PER_POST, expand_tabs=False, replace_whitespace=False
    )

    text_processing_pipeline: Pipe[str] = (
        Pipe()
        | str.strip
        | partial(space_regex.sub, " ")
        | partial(space_before_punctuation.sub, "")
        | partial(three_dots.sub, "…")
        | disnake.utils.escape_markdown
    )

    def __init__(
        self,
        text: str = "",
        images: Iterable[Image] | None = None,
        embeds: Iterable[Embed] | None = None,
    ) -> None:
        self.text = text
        self.images = images or []
        self.embeds = embeds or []

    @classmethod
    def _wrap_text(cls, text: str) -> list[str]:
        if len(text) <= MAX_CHARACTERS_PER_POST:
            return [text]

        return cls.wrapper.wrap(text)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.processed_text = self._wrap_text(self.text_processing_pipeline(value))

    async def send(self) -> None:
        pass

    async def respond(self) -> None:
        pass

    def prepare_messages(self) -> list[Message]:
        pass
