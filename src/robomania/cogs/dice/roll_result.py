from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Union, cast, overload

import numpy as np

T = TypeVar('T', bound=Union[int, list])


@dataclass(init=False)
class RollResult(Generic[T]):
    value: T

    def __init__(self, value: T | RollResult[T]) -> None:
        if isinstance(value, RollResult):
            # Assign without copying, might cause bugs
            self.value = value.value
        else:
            self.value = value

    def sum(self) -> RollResult:
        return RollResult(self.__sum())

    def __sum(self) -> int:
        if isinstance(self.value, int):
            v = self.value
        else:
            v = np.sum(self.value)  # type: ignore

        return v

    def __int__(self) -> int:
        out: int
        v = self.value
        match v:
            case int():
                out = v
            case list():
                out = sum(int(i) for i in v)

        return out

    def __concat(self: RollResult[list], other: list) -> list:
        if isinstance(self.value, int):
            raise ValueError('Cannot concat with int')
        else:
            out = self.value.copy()
            out.extend(other)
            return out

    def __neg__(self) -> RollResult:
        if isinstance(self.value, list):
            raise ValueError('Cannot negate a list')

        return RollResult(-cast(int, self.value))

    def finalize(self) -> int | list:
        if isinstance(self.value, int):
            return self.value

        out: list[int | list] = []
        for i in cast(list, self.value):
            if isinstance(i, RollResult):
                out.append(i.finalize())
            else:
                out.append(cast(int | list, i))

        return out

    @overload
    def __add__(
        self: RollResult[list],
        other: int | RollResult[int]
    ) -> RollResult[int]:
        pass

    @overload
    def __add__(
        self: RollResult[list],
        other: list | RollResult[list]
    ) -> RollResult[list]:
        pass

    @overload
    def __add__(
        self: RollResult[int],
        other: int | list | RollResult[int]
    ) -> RollResult[int]:
        pass

    def __add__(self, other: object):
        out: int | list
        match other:
            case int():
                out = self.__sum() + other
            case list() if isinstance(self.value, int):
                out = self.value + sum(other)
            case list():
                out = cast(RollResult[list], self).__concat(other)
            case RollResult(value=int()):
                out = self.__sum() + cast(int, other.value)
            case RollResult(list()) if isinstance(self.value, int):
                out = self.value + other.__sum()
            case RollResult(list()):
                out = cast(
                    RollResult[list], self
                ).__concat(cast(RollResult[list], other).value)
            case _:
                raise ValueError(f'+ opperator not supported: "{other!r}"')

        return RollResult(out)

    @overload
    def __radd__(
        self: RollResult[int],
        other: int | list
    ) -> RollResult[int]:
        pass

    @overload
    def __radd__(
        self: RollResult[list],
        other: int
    ) -> RollResult[int]:
        pass

    @overload
    def __radd__(
        self: RollResult[list],
        other: list
    ) -> RollResult[list]:
        pass

    def __radd__(self, other: Any):
        if isinstance(other, (int, list)):
            return RollResult(other) + self  # type: ignore

        raise ValueError(f'+ operator not supported: "{other}"')

    def __sub__(self, other: object) -> RollResult:
        out: int
        self_value = self.__sum()
        match other:
            case int():
                out = other
            case list():
                out = sum(other)
            case RollResult():
                out = other.__sum()
            case _:
                raise ValueError(f'- operator not supported: "{other!r}"')

        return RollResult(self_value - out)

    def __rsub__(self, other: object) -> RollResult:
        return -self.__sub__(other)
