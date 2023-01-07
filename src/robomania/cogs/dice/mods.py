from __future__ import annotations

from typing import TYPE_CHECKING, cast

from robomania.cogs.dice.roll_result import RollResult

if TYPE_CHECKING:
    from robomania.cogs.dice.dice import Dice, DiceExpression


def mod_repeat(expression: DiceExpression, argument: int | None) -> RollResult:
    if argument is None or argument <= 0:
        raise ValueError(
            'Repeat requires positive argument.',
            'DICE_REPEAT_ARGUMENT',
        )

    return RollResult([expression.eval() for _ in range(argument)])


def mod_explode(
    expression: DiceExpression,
    argument: int | None
) -> RollResult:
    dice = cast('Dice', expression)
    try:
        num_of_explosions = dice.num_of_dice
    except AttributeError:
        try:
            if dice.mod.value == '!':  # type: ignore
                return dice.eval()
        except AttributeError:
            pass
        raise ValueError(
            'Cannot explode a group.',
            'DICE_EXPLOSION_DICE_ONLY'
        )

    out: RollResult[list[int]] = RollResult([])

    while True:
        roll = dice._roll(dice.base, num_of_explosions)
        out = out + roll
        num_of_explosions = roll.count(dice.base)
        if num_of_explosions == 0:
            break

    return out


def mod_sum(
    expression: DiceExpression,
    argument: int | None
) -> RollResult:
    value = expression.eval()
    return value.sum()


def mod_drop_low(
    expression: DiceExpression,
    argument: int | None
) -> RollResult:
    if argument is None or argument <= 0:
        raise ValueError(
            'Drop low required positive argument.',
            'DICE_DROP_LOW_ARGUMENT'
        )

    value: RollResult[int | list[int | list]] = expression.eval()

    if isinstance(value.value, int):
        return value

    if len(value.value) <= argument:
        return RollResult(0)

    indexes_to_remove = [
        i[0]
        for i
        in sorted(
            enumerate(value.value),
            key=lambda x: int(RollResult(x[1])),  # type: ignore
            reverse=True
        )
    ][:argument]
    indexes_to_remove.sort(reverse=True)

    for i in indexes_to_remove:
        value.value.pop(i)

    return value


def mod_keep_high(
    expression: DiceExpression,
    argument: int | None
) -> RollResult:
    if argument is None or argument <= 0:
        raise ValueError(
            'Keep high required positive argument.',
            'DICE_KEEP_HIGH_ARGUMENT'
        )

    value: RollResult[int | list[int | list]] = expression.eval()

    if isinstance(value.value, int) or len(value.value) <= argument:
        return value

    indexes_to_remove = [
        i[0]
        for i
        in sorted(
            enumerate(value.value),
            key=lambda x: int(RollResult(x[1]))  # type: ignore
        )
    ][:argument]
    indexes_to_remove.sort(reverse=True)

    for i in indexes_to_remove:
        value.value.pop(i)

    return value
