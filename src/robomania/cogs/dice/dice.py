from __future__ import annotations

import enum
import operator
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, TypeAlias

import numpy as np

from robomania.cogs.dice.mods import (
    mod_drop_low,
    mod_explode,
    mod_keep_high,
    mod_repeat,
    mod_sum,
)
from robomania.cogs.dice.roll_result import RollResult


class ModEnum(str, enum.Enum):
    priority: int
    # `Any` shouldn't be as first argument, but mypy thinks it's a method,
    # and complains about number of arguments
    func: Callable[[Any, "DiceExpression", int | None], RollResult]

    EXPLODE = ("!", 0, mod_explode)
    KEEP_HIGH = ("kh", 10, mod_keep_high)
    DISCARD_LOW = ("dl", 10, mod_drop_low)
    REPEAT = ("@", 10, mod_repeat)
    SUM = ("s", 10, mod_sum)

    def __new__(cls, value: str, priority: int, func: Callable[["DiceExpression", int | None], RollResult]) -> ModEnum:
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.priority = priority
        obj.func = func  # type: ignore
        return obj

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self._name_}"


class OperatorEnum(str, enum.Enum):
    # Should be only two `Any`, but mypy thinks it's a method, and complains
    # about number of arguments
    func: Callable[[Any, Any, Any], Any]

    PLUS = ("+", operator.add)
    MINUS = ("-", operator.sub)
    MUL = ("*", operator.mul)
    DIV = ("/", operator.truediv)
    NONE = ("", lambda a, b: None)

    def __new__(cls, value: str, func: Callable[[Any, Any], Any]) -> OperatorEnum:
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.func = func  # type: ignore
        return obj

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self._name_}"

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
        return [int(i) for i in np.random.randint(1, base + 1, num_of_dice, np.uint64)]

    def __str__(self) -> str:
        return f'{self.num_of_dice if self.num_of_dice else ""}d{self.base}'


@dataclass
class Mod:
    dice_expression: DiceExpression = field(init=False)
    mod: ModEnum
    argument: int | None = field(default=None)

    def set_dice_expression(self, dice_expression: DiceExpression) -> None:
        self.dice_expression = dice_expression

    def eval(self) -> RollResult:
        return self.mod.func(self.dice_expression, self.argument)

    def __str__(self) -> str:
        argument_str = "" if self.argument is None else str(self.argument)
        return f"{self.dice_expression}{self.mod.value}{argument_str}"


@dataclass
class Expression:
    values: list[Value]
    operators: list[OperatorEnum]

    def eval(self) -> RollResult:
        values = deque(self.values)
        operators = deque(self.operators)

        value = values.popleft().eval()

        while values:
            right_value = values.popleft().eval()
            operator = operators.popleft()

            value = operator.func(value, right_value)

        return RollResult(value)

    def __str__(self) -> str:
        values = deque(self.values)
        operators = deque(self.operators)

        out = []

        while values:
            out.append(str(values.popleft()))

            if values:
                out.append(operators.popleft().value)

        return "".join(out)


@dataclass
class Sequence:
    values: list[Expression]

    def eval(self) -> RollResult:
        return RollResult([i.eval() for i in self.values])

    def __str__(self) -> str:
        body_of_sequence = ", ".join(str(i) for i in self.values)
        return f"{{{body_of_sequence}}}"


DiceExpression: TypeAlias = Dice | Sequence | Mod


@dataclass
class Value:
    value: DiceExpression | int | Expression
    unary_operator: OperatorEnum = field(default=OperatorEnum.NONE)

    def eval(self) -> RollResult:
        if isinstance(self.value, int):
            out = RollResult(self.value)
        else:
            out = self.value.eval()

        if self.unary_operator is OperatorEnum.MINUS:
            out = -out

        return out

    def __str__(self) -> str:
        if isinstance(self.value, Expression):
            value = f"({self.value})"
        else:
            value = str(self.value)
        return f"{self.unary_operator.value}{value}"


@dataclass
class Roll:
    expressions: list[Expression]

    def eval(self) -> RollResult:
        return RollResult(self.eval_to_list())

    def eval_to_list(self) -> list[RollResult]:
        return [i.eval() for i in self.expressions]

    def __str__(self) -> str:
        return ", ".join(str(i) for i in self.expressions)
