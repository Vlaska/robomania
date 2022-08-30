from __future__ import annotations

import contextlib
import io
from typing import Generator, Protocol, Type, TypeVar


class Preconfigurable(Protocol):
    @staticmethod
    def preconfigure() -> None:
        raise NotImplementedError


_preconfigurable = TypeVar('_preconfigurable', bound=Preconfigurable)


@contextlib.contextmanager
def rewindable_buffer(
    *args: io.BytesIO
) -> Generator[tuple[io.BytesIO, ...], None, None]:
    try:
        yield args
    finally:
        for buffer in args:
            buffer.seek(0)


def preconfigure(cls: Type[_preconfigurable]) -> Type[_preconfigurable]:
    if getattr(cls, 'preconfigure'):
        cls.preconfigure()

    return cls
