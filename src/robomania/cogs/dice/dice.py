from __future__ import annotations

import enum
import operator
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, TypeAlias, cast

import numpy as np

from robomania.cogs.dice.roll_result import RollResult


class ModEnum(str, enum.Enum):
    priority: int

    EXPLODE = ('!', 0)
    KEEP_HIGH = ('kh', 10)
    DISCARD_LOW = ('dl', 10)
    REPEAT = ('@', 20)
    SUM = ('s', 20)

    def __new__(cls, value: str, priority: int) -> ModEnum:
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.priority = priority
        return obj

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self._name_}'


class OperatorEnum(str, enum.Enum):
    func: Callable[[Any, Any], Any]

    PLUS = ('+', operator.add)
    MINUS = ('-', operator.sub)
    MUL = ('*', operator.mul)
    DIV = ('/', operator.truediv)
    NONE = ('', lambda a, b: None)

    def __new__(
        cls,
        value: str,
        func: Callable[[Any, Any], Any]
    ) -> OperatorEnum:
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.func = func  # type: ignore
        return obj

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self._name_}'

    @classmethod
    def _missing_(cls, value: object) -> OperatorEnum:
        return cls.NONE


@dataclass
class Dice:
    base: int
    num_of_dice: int = field(default=1)

    def eval(self) -> RollResult:
        return RollResult(self._roll(self.base, self.num_of_dice))

    @staticmethod
    def _roll(base: int, num_of_dice: int) -> list[int]:
        return cast(
            list[int],
            np.random.randint(1, base + 1, num_of_dice, np.uint64)
        )

    def __str__(self) -> str:
        return f'{self.num_of_dice if self.num_of_dice else ""}d{self.base}'


@dataclass
class Mod:
    dice_expression: DiceExpression | None = field(init=False, default=None)
    mod: ModEnum
    argument: int | None = field(default=None)

    def set_dice_expression(self, dice_expression: DiceExpression) -> None:
        self.dice_expression = dice_expression

    def eval(self) -> RollResult:
        pass

    def __str__(self) -> str:
        argument_str = '' if self.argument is None else str(self.argument)
        try:
            return f'{self.dice_expression}{self.mod.value}{argument_str}'
        except AttributeError:
            return f'{self.mod.value}{argument_str}'


@dataclass
class Expression:
    values: list[Value]
    operators: list[OperatorEnum]

    def eval(self) -> RollResult:
        pass

    def __str__(self) -> str:
        values = deque(self.values)
        operators = deque(self.operators)

        out = []

        while values:
            out.append(str(values.popleft()))

            if values:
                out.append(operators.popleft().value)

        return ''.join(out)


@dataclass
class Sequence:
    values: list[Expression]

    def eval(self) -> RollResult:
        pass

    def __str__(self) -> str:
        body_of_sequence = ', '.join(str(i) for i in self.values)
        return f'{{{body_of_sequence}}}'


DiceExpression: TypeAlias = Dice | Sequence | Mod


@dataclass
class Value:
    value: DiceExpression | int | Expression
    unary_operator: OperatorEnum = field(default=OperatorEnum.NONE)

    def eval(self) -> RollResult:
        pass

    def __str__(self) -> str:
        if isinstance(self.value, Expression):
            value = f'({self.value})'
        else:
            value = str(self.value)
        return f'{self.unary_operator.value}{value}'


@dataclass
class Roll:
    expressions: list[Expression]

    def eval(self) -> list[RollResult]:
        return [i.eval() for i in self.expressions]

    def __str__(self) -> str:
        return ', '.join(str(i) for i in self.expressions)
