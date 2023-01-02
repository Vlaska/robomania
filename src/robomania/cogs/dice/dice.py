from __future__ import annotations

from dataclasses import dataclass, field
from random import randint
from typing import Optional


@dataclass
class DiceBase:
    base: int
    multiplyer: Optional[int] = field(default=1)

    def calc(self) -> int:
        if self.base == 0:
            return 0
        return sum(randint(self.base) + 1 for _ in range(self.multiplyer))


@dataclass
class DiceWithModifier:
    dice: DiceBase
    modifier: int
