from __future__ import annotations

import warnings
from dataclasses import dataclass
from logging import getLogger
from typing import Generic, TypeVar, Union, cast, overload

import numpy as np

T = TypeVar('T', bound=Union[int, list])
logger = getLogger('robomania.cogs.dice')


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
            v = int(np.sum(self.value))  # type: ignore

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

    def __concat(
        self: RollResult[list],
        other: list | RollResult[list]
    ) -> list:
        if isinstance(self.value, int):
            raise ValueError('Cannot concat with int')
        else:
            if isinstance(other, RollResult):
                other = other.value

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

        if len(out) == 1:
            return out[0]

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
            case RollResult(value=int()):
                out = self.__sum() + cast(int, other.value)
            case RollResult(list()) if isinstance(self.value, int):
                out = self.value + other.__sum()
            case list() | RollResult(list()):
                out = cast(
                    RollResult[list], self
                ).__concat(other)
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

    def __radd__(self, other):
        if isinstance(other, (int, list)):
            return RollResult(other) + self

        raise ValueError(f'+ operator not supported: "{other}"')

    @staticmethod
    def __transform_other_to_int(
        other: int | list | RollResult[int | list],
        exception_message: str = 'Cannot transform to int'
    ) -> int:
        match other:
            case int():
                out = other
            case list():
                out = sum(other)
            case RollResult():
                out = other.__sum()
            case _:
                raise ValueError(f'{exception_message}: "{other!r}"')

        return out

    def __sub__(
        self,
        other: int | list | RollResult[int | list]
    ) -> RollResult[int]:
        out = self.__transform_other_to_int(
            other,
            '- operator not supported'
        )
        self_value = self.__sum()

        return RollResult(self_value - out)

    def __rsub__(self, other: int | list) -> RollResult[int]:
        return -self.__sub__(other)

    def __mul__(
        self,
        other: int | list | RollResult[int | list]
    ) -> RollResult[int]:
        out = self.__transform_other_to_int(
            other,
            '* operator not supported'
        )
        self_value = self.__sum()
        return RollResult(self_value * out)

    def __rmul__(self, other: int | list) -> RollResult[int]:
        return self * other

    def __truediv__(
        self,
        other: int | list | RollResult[int | list]
    ) -> RollResult[int]:
        out = self.__transform_other_to_int(other)
        self_value = self.__sum()
        if out == 0:
            if (isinstance(other, int) or (isinstance(
                    other, RollResult) and isinstance(other.value, int))):
                raise ZeroDivisionError('Cannot divide by 0')
            else:
                warnings.warn(
                    'Roll result or list evaluated to 0 during division',
                    UserWarning
                )
                logger.warning(
                    'Roll result or list evaluated to 0 during division, '
                    'aborting division.'
                )
                out = 1

        return RollResult(self_value // out)

    def __rtruediv__(
        self,
        other: int | list
    ) -> RollResult[int]:
        out = self.__transform_other_to_int(other)
        self_value = self.__sum()
        if self_value == 0:
            if isinstance(self.value, int):
                raise ZeroDivisionError('Cannot divide by 0')
            else:
                warnings.warn(
                    'Roll result or list evaluated to 0 during division',
                    UserWarning
                )
                logger.warning(
                    'Roll result or list evaluated to 0 during division, '
                    'aborting division.'
                )
                self_value = 1

        return RollResult(out // self_value)
