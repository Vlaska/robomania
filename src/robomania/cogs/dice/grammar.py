from __future__ import annotations

from arpeggio import EOF, OneOrMore, Optional, PTNodeVisitor
from arpeggio import RegExMatch as _

from robomania.cogs.dice.dice import DiceBase, DiceWithModifier


def number():
    return _(r'\d+')


def dice_marker():
    return _(r'k|d')


def dice_base():
    return Optional(number), dice_marker, number


def sign():
    return Optional(['+', '-'])


def dice_with_mod():
    return dice_base, sign, number


def dices():
    return Optional([dice_with_mod, dice_base])


def dice():
    return OneOrMore(dices), EOF


class DiceVisitor(PTNodeVisitor):
    def visit_number(self, node, children) -> int:
        return int(node.value)

    def visit_dice_base(self, node, children: list[int]) -> DiceBase:
        if len(children) == 2:
            multiplyer = 1
            base = children[1]
        else:
            multiplyer, _, base = children

        return DiceBase(multiplyer=multiplyer, base=base)

    def visit_dice_with_mod(self, node, children) -> DiceWithModifier:
        dice: DiceBase
        sign: str
        mod: int
        print(children)
        dice, sign, mod = children

        if sign == '-':
            mod *= -1

        return DiceWithModifier(dice, mod)

    def visit_dice(self, node, children):
        return children
