from __future__ import annotations

import pytest

from robomania.cogs.dice.roll_result import RollResult

b_l = [1, 2, 3]
b_l2 = [4, 5, 6]


@pytest.mark.parametrize('left, right, out', [
    pytest.param(
        1, RollResult(2), RollResult(3),
        id='int + RR(int)'
    ),
    pytest.param(
        RollResult(1), RollResult(2), RollResult(3),
        id='RR(int) + RR(int)'
    ),
    pytest.param(
        1, RollResult(b_l), RollResult(7),
        id='int + RR(list[int])'
    ),
    pytest.param(
        b_l2, RollResult(1), RollResult(16),
        id='list[int] + RR(int)'
    ),
    pytest.param(
        b_l2, RollResult(b_l), RollResult([4, 5, 6, 1, 2, 3]),
        id='list[int] + RR(list[int])'
    ),
    pytest.param(
        RollResult(1), RollResult(b_l), RollResult(7),
        id='RR(int) + RR(list[int])'
    ),
    pytest.param(
        RollResult(b_l), RollResult(b_l2), RollResult([1, 2, 3, 4, 5, 6]),
        id='RR(list[int]) + RR(list[int])'
    ),
    pytest.param(
        1, RollResult([RollResult(1), RollResult(2)]), RollResult(4),
        id='int + RR(list[RR(int)])'
    ),
    pytest.param(
        1, RollResult([RollResult(b_l), RollResult(b_l2)]), RollResult(22),
        id='int + RR(list[RR(list[int])])'
    ),
    pytest.param(
        RollResult(b_l),
        RollResult([RollResult(b_l), RollResult(b_l2)]),
        RollResult([1, 2, 3, RollResult(b_l), RollResult(b_l2)]),
        id='RR(list[int]) + RR(list[RR(list[int])])'
    ),
])
def test_add(left, right, out) -> None:
    assert left + right == out


@pytest.mark.parametrize('left, right, out', [
    pytest.param(
        1, RollResult(2), RollResult(-1),
        id='int - RR(int)'
    ),
    pytest.param(
        RollResult(2), 1, RollResult(1),
        id='RR(int) - int'
    ),
    pytest.param(
        RollResult(1), RollResult(2), RollResult(-1),
        id='RR(int) - RR(int)'
    ),
    pytest.param(
        1, RollResult(b_l), RollResult(-5),
        id='int - RR(list[int])'
    ),
    pytest.param(
        RollResult(1), RollResult(b_l), RollResult(-5),
        id='RR(int) - RR(list[int])'
    ),
    pytest.param(
        RollResult(b_l), RollResult(b_l2), RollResult(-9),
        id='RR(list[int]) - RR(list[int])'
    ),
    pytest.param(
        1, RollResult([RollResult(1), RollResult(2)]), RollResult(-2),
        id='int - RR(list[RR(int)])'
    ),
    pytest.param(
        1, RollResult([RollResult(b_l), RollResult(b_l2)]), RollResult(-20),
        id='int - RR(list[RR(list[int])])'
    ),
    pytest.param(
        RollResult([RollResult(b_l), RollResult(b_l2)]), 1, RollResult(20),
        id='RR(list[RR(list[int])]) - int'
    ),

    pytest.param(
        b_l2, RollResult(1), RollResult(14),
        id='list[int] - RR(int)'
    ),
    pytest.param(
        b_l2, RollResult(b_l), RollResult(9),
        id='list[int] - RR(list[int])'
    ),
])
def test_sub(left, right, out) -> None:
    assert left - right == out


@pytest.mark.parametrize('t, result', [
    (RollResult(1), 1),
    (RollResult(b_l), b_l),
    (RollResult([b_l, b_l2]), [b_l, b_l2]),
    (RollResult([1, RollResult([2, 3, RollResult(4)])]), [1, [2, 3, 4]]),
])
def test_finalize(t: RollResult, result) -> None:
    assert t.finalize() == result
