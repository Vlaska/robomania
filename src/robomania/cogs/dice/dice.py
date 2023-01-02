from __future__ import annotations

from dataclasses import dataclass, field
from random import randint


@dataclass
class DiceBase:
    base: int
    num_of_dice: int = field(default=1)

    def calc(self) -> int:
        if self.base == 0:
            return 0
        return sum(
            (randint(1, self.base + 1)) for _ in range(self.num_of_dice)
        )

    def __str__(self) -> str:
        return f'{self.num_of_dice if self.num_of_dice else ""}d{self.base}'


@dataclass
class DiceWithModifier:
    dice: DiceBase
    modifier: int

    def calc(self) -> int:
        return self.dice.calc() + self.modifier

    def __str__(self) -> str:
        if self.modifier < 0:
            mod = f'- {abs(self.modifier)}'
        else:
            mod = f'+ {self.modifier}'
        return f'{self.dice} {mod}'
