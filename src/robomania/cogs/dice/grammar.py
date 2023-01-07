from __future__ import annotations

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.cleanpeg import ParserPEG

from robomania.cogs.dice.dice import (Dice, DiceExpression, Expression, Mod,
                                      ModEnum, OperatorEnum, Roll, Sequence,
                                      Value)

grammar = r"""
number = r'\d+'
dice = number? r'd|k' number
keep_discard = r'dl?' / r'kh?'
explode = '!'
repeat = "@" / "r"
sum = "s"
mod = (keep_discard / explode / repeat / sum) number?

dice_expression = (sequence / dice) mod*

unary_operator = "+" / "-"
binary_plus_minus = "+" / "-"
binary_mul_div = "*" / "/"

value = unary_operator? (dice_expression / number / ("(" expression ")"))

sequence = "{" expression ("," expression)* "}"

term = value (binary_mul_div term)*
expression = term (binary_plus_minus term)*
roll = expression ("," expression)* EOF
"""


grammar_parser = ParserPEG(grammar, 'roll')


class DiceVisitor(PTNodeVisitor):
    def visit_number(self, node, children) -> int:
        return int(node.value)

    def visit_dice(self, node, children: list[int]) -> Dice:
        if len(children) == 2:
            multiplyer = 1
            base = children[1]
        else:
            multiplyer, _, base = children

        return Dice(base=base, num_of_dice=multiplyer)

    def visit_keep_discard(self, node, children) -> ModEnum:
        match children[0]:
            case 'd' | 'dl':
                return ModEnum.DISCARD_LOW
            case 'k' | 'kh':
                return ModEnum.KEEP_HIGH
            case _:
                raise ValueError('WTF?', 'WTF?')

    def visit_sum(self, node, children) -> ModEnum:
        return ModEnum.SUM

    def visit_explode(self, node, children) -> ModEnum:
        return ModEnum.EXPLODE

    def visit_repeat(self, node, children) -> ModEnum:
        return ModEnum.REPEAT

    def visit_mod(self, node, children) -> Mod:
        mod = children[0]

        if len(children) == 2:
            argument = children[1]
        else:
            argument = None

        return Mod(mod, argument)

    def visit_dice_expression(self, node, children) -> DiceExpression:
        dice_expression: DiceExpression
        mod: list[Mod]
        dice_expression, *mod = children

        mod.sort(key=lambda x: x.mod.priority)

        for i in mod:
            i.set_dice_expression(dice_expression)
            dice_expression = i

        return dice_expression

    def visit_unary_operator(self, node, children) -> OperatorEnum:
        return OperatorEnum(children[0])  # type: ignore

    def visit_binary_plus_minus(self, node, children) -> OperatorEnum:
        return OperatorEnum(children[0])  # type: ignore

    def visit_binary_mul_div(self, node, children) -> OperatorEnum:
        return OperatorEnum(children[0])  # type: ignore

    def visit_value(self, node, children) -> Value:
        unary: OperatorEnum = OperatorEnum.NONE
        v = children[-1]
        if len(children) == 2:
            unary = children[0]

        return Value(v, unary)

    def visit_sequence(self, node, children) -> Sequence:
        return Sequence(list(children))

    def visit_term(self, node, children) -> Expression:
        values: list[Value] = children[::2]
        operators: list[OperatorEnum] = children[1::2]

        return Expression(values, operators)

    def visit_expression(self, node, children) -> Expression:
        values: list[Value] = children[::2]
        operators: list[OperatorEnum] = children[1::2]

        return Expression(values, operators)

    def visit_roll(self, node, children) -> Roll:
        return Roll(list(children))


def parse(dice: str) -> Roll:
    tree = grammar_parser.parse(dice)
    return visit_parse_tree(tree, DiceVisitor())
