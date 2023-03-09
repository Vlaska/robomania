from __future__ import annotations

from functools import reduce
from typing import Any, Callable

PipeStage = Callable[[Any], Any]


class Pipe:
    pipeline: list[PipeStage]

    def __init__(self, *args: PipeStage) -> None:
        self.pipeline = []
        self.pipeline.extend(args)

    def copy(self) -> Pipe:
        return Pipe(*self.pipeline)

    def add(self, func: PipeStage) -> Pipe:
        return self.__or__(func)

    def __or__(self, func: PipeStage) -> Pipe:
        self.pipeline.append(func)
        return self

    def __ror__(self, func: PipeStage) -> Pipe:
        out = Pipe(func)
        out.pipeline.extend(self.pipeline)
        return out

    def __call__(self, x: Any) -> Any:
        return reduce(lambda v, func: func(v), self.pipeline, x)
