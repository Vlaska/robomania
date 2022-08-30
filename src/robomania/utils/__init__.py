from __future__ import annotations

import contextlib
import inspect
import logging
from typing import BinaryIO, Generator, Protocol, TextIO, Type, TypeVar

logger = logging.getLogger('robomania')


class Preconfigurable(Protocol):
    @staticmethod
    def preconfigure() -> None:
        raise NotImplementedError


_preconfigurable = TypeVar('_preconfigurable', bound=Preconfigurable)
Buffer = TypeVar('Buffer', bound=TextIO | BinaryIO)


@contextlib.contextmanager
def rewindable_buffer(
    *args: Buffer
) -> Generator[tuple[Buffer, ...], None, None]:
    try:
        yield args
    finally:
        for buffer in args:
            buffer.seek(0)


def preconfigure(cls: Type[_preconfigurable]) -> Type[_preconfigurable]:
    try:
        cls.preconfigure()
    except AttributeError:
        file = inspect.getfile(cls)
        logger.error(f'Preconfiguration method missing: {file}:{cls.__name__}')

    return cls
