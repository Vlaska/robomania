from __future__ import annotations

from contextlib import nullcontext as does_not_raise

import pytest

from robomania.cogs.dice.roll_result import RollResult

base_params = [
    (1, 2),
    (1, [2, 3]),
    (1, RollResult(2)),
    (1, RollResult([2, 3])),
    ([1, 2], 3),
    ([1, 2, 3], [4, 5, 6]),
    ([1, 2, 3], RollResult(4)),
    ([1, 2, 3], RollResult([4, 5, 6])),
]


def gen_params(results: list) -> list:
    if len(base_params) != len(results):
        raise ValueError("Missing param results")

    return [(i[0], i[1], j) for i, j in zip(base_params, results)]


addition_params = gen_params([3, 6, 3, 6, 6, [1, 2, 3, 4, 5, 6], 10, [1, 2, 3, 4, 5, 6]])

right_addition_params = gen_params(
    [
        3,
        6,
        3,
        6,
        6,
        [4, 5, 6, 1, 2, 3],
        10,
        [4, 5, 6, 1, 2, 3],
    ]
)

sub_params = gen_params([-1, -4, -1, -4, 0, -9, 2, -9])

right_sub_params = gen_params([1, 4, 1, 4, 0, 9, -2, 9])

mul_params = gen_params([2, 5, 2, 5, 9, 90, 24, 90])


@pytest.mark.parametrize(("left", "right", "result"), addition_params)
def test_addition(left, right, result) -> None:
    assert (RollResult(left) + right).value == result


@pytest.mark.parametrize(("right", "left", "result"), right_addition_params)
def test_right_addition(left, right, result) -> None:
    assert (left + RollResult(right)).value == result


@pytest.mark.parametrize(("left", "right", "result"), sub_params)
def test_sub(left, right, result) -> None:
    assert (RollResult(left) - right).value == result


@pytest.mark.parametrize(("right", "left", "result"), right_sub_params)
def test_right_sub(right, left, result) -> None:
    assert (left - RollResult(right)).value == result


@pytest.mark.parametrize(("left", "right", "result"), mul_params)
def test_mul(left, right, result) -> None:
    assert (RollResult(left) * right).value == result


@pytest.mark.parametrize(("right", "left", "result"), mul_params)
def test_right_mul(right, left, result) -> None:
    assert (left * RollResult(right)).value == result


@pytest.mark.parametrize(
    ("left", "right", "result"),
    [
        (10, 5, 2),
        (11, 5, 2),
        (10, [1, 2], 3),
        (10, RollResult(5), 2),
        (10, RollResult([1, 2]), 3),
        ([3, 2, 5], 5, 2),
        ([3, 2, 5], [1, 2], 3),
        ([3, 2, 5], RollResult(5), 2),
        ([3, 2, 5], RollResult([1, 2]), 3),
    ],
)
def test_div(left, right, result) -> None:
    assert (RollResult(left) / right).value == result


@pytest.mark.parametrize(
    ("left", "right", "result"),
    [
        (10, 5, 2),
        (11, 5, 2),
        ([2, 3, 5], 5, 2),
        (RollResult(10), 5, 2),
        (RollResult([2, 3, 5]), 5, 2),
        (10, [2, 3], 2),
        ([2, 3, 5], [2, 3], 2),
        (RollResult(10), [2, 3], 2),
        (RollResult([2, 3, 5]), [2, 3], 2),
    ],
)
def test_right_div(left, right, result) -> None:
    assert (left / RollResult(right)).value == result


@pytest.mark.parametrize(
    ("right", "raises"),
    [
        (0, pytest.raises(ZeroDivisionError)),
        ([0], does_not_raise()),
        ([-1, 2], does_not_raise()),
        (RollResult(0), pytest.raises(ZeroDivisionError)),
        (RollResult([-1, 2]), does_not_raise()),
        (RollResult([0]), does_not_raise()),
    ],
)
def test_div_by_zero(right, raises) -> None:
    with raises:
        assert (RollResult(10) / right).value == 10


@pytest.mark.parametrize(
    ("right", "raises"),
    [
        (0, pytest.raises(ZeroDivisionError)),
        ([0], does_not_raise()),
        ([-1, 2], does_not_raise()),
    ],
)
def test_right_div_by_zero(right, raises) -> None:
    with raises:
        assert (10 / RollResult(right)).value == 10


@pytest.mark.parametrize(
    ("t", "result"),
    [
        (1, 1),
        ([1, 2, 3], [1, 2, 3]),
        ([[1, 2, 3], RollResult([4, 5, RollResult(6)])], [[1, 2, 3], [4, 5, 6]]),
    ],
)
def test_finalize(t: RollResult, result) -> None:
    assert RollResult(t).finalize() == result


@pytest.mark.parametrize(
    ("value", "result"),
    [
        (1, 1),
        ([1], [1]),
        ([1, RollResult(2)], [1, RollResult(2)]),
        (RollResult(1), 1),
        (RollResult([1]), [1]),
    ],
)
def test_init(value, result) -> None:
    assert RollResult(value).value == result


@pytest.mark.parametrize(
    ("value", "result"),
    [
        (1, 1),
        ([1, 2, 3], 6),
        ([1, 2, 3, RollResult(4)], 10),
        ([1, 2, 3, RollResult([4, 5, 6])], 21),
    ],
)
def test_int(value, result) -> None:
    assert int(RollResult(value)) == result


@pytest.mark.parametrize(
    ("value", "result"),
    [
        (1, 1),
        ([1, 2, 3], 6),
        ([1, 2, 3, RollResult(4)], 10),
        ([1, 2, 3, RollResult([4, 5, 6])], 21),
    ],
)
def test_protected_sum(value, result) -> None:
    assert RollResult(value)._RollResult__sum() == result


def test_neg() -> None:
    assert -RollResult(5).value == -5

    with pytest.raises(ValueError):
        -RollResult([5])


def test_concat() -> None:
    value = RollResult([1, 2, 3])
    other = [4, 5, 6]
    result = [1, 2, 3, 4, 5, 6]

    with pytest.raises(ValueError):
        RollResult(5)._RollResult__concat(other)

    assert value._RollResult__concat(other) == result
    assert value._RollResult__concat(RollResult(other)) == result


@pytest.mark.parametrize(
    ("value", "raises", "result"),
    [
        (1, does_not_raise(), 1),
        ([1, 2, 3], does_not_raise(), 6),
        (RollResult(1), does_not_raise(), 1),
        (RollResult([1, 2, RollResult(3)]), does_not_raise(), 6),
        ({42}, pytest.raises(ValueError, match="Custom message"), None),
    ],
)
def test_transform_other_to_int(value, raises, result) -> None:
    with raises:
        assert RollResult._RollResult__transform_other_to_int(value, "Custom message") == result
