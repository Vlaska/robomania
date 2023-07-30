from __future__ import annotations

import contextlib
import inspect
import logging
from typing import TYPE_CHECKING, BinaryIO, Protocol, TextIO, TypeVar

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger("robomania.utils")


class Preconfigurable(Protocol):
    @staticmethod
    def preconfigure() -> None:
        raise NotImplementedError


_preconfigurable = TypeVar("_preconfigurable", bound=Preconfigurable)
Buffer = TypeVar("Buffer", bound=TextIO | BinaryIO)


@contextlib.contextmanager
def rewindable_buffer(*args: Buffer) -> Generator[tuple[Buffer, ...], None, None]:
    try:
        yield args
    finally:
        for buffer in args:
            buffer.seek(0)


def preconfigure(cls: type[_preconfigurable]) -> type[_preconfigurable]:
    try:
        cls.preconfigure()
    except AttributeError:
        file = inspect.getfile(cls)
        logger.exception(f"Preconfiguration method missing: {file}:{cls.__name__}")

    return cls
