import pytest

from robomania.cogs.dice.grammar import parse


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        ("{1, 2, 3, 4, 5}k2", [4, 5]),
        ("{{1, 2}, {3, 4}, 5}k2", [[3, 4], 5]),
        ("{1, 2, 3, 4, 5}k10", [1, 2, 3, 4, 5]),
    ],
)
def test_keep_high(expression, result) -> None:
    assert parse(expression).eval().finalize() == result


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        ("{1, 2, 3, 4, 5}d2", [3, 4, 5]),
        ("{{1, 2}, {3, 4}, 5}d2", [3, 4]),
        ("{1, 2, 3, 4, 5}d10", 0),
    ],
)
def test_drop_low(expression, result) -> None:
    assert parse(expression).eval().finalize() == result


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        ("{1, 2, 3, 4, 5}s", 15),
        ("{1, 2, {3, 4, 5}}s", 15),
    ],
)
def test_sum(expression, result) -> None:
    assert parse(expression).eval().finalize() == result


def test_explode() -> None:
    assert parse("5d2!").eval().finalize() == [
        1,
        2,
        2,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        1,
        1,
        2,
        1,
    ]


def test_double_explode() -> None:
    assert parse("5d2!!").eval().finalize() == [
        1,
        2,
        2,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        1,
        1,
        2,
        1,
    ]


def test_explode_sequence() -> None:
    with pytest.raises(ValueError, match="Cannot explode a group."):
        parse("{1, 2}!").eval()


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        ("2d3@2", [[1, 2], [1, 2]]),
        ("{1, 2}@2", [[1, 2], [1, 2]]),
        ("{1, 2}@2@2", [[[1, 2], [1, 2]], [[1, 2], [1, 2]]]),
        ("{2d3, 3d5}@2", [[[1, 2], [1, 4, 4]], [[2, 2], [3, 5, 1]]]),
    ],
)
def test_repeat(expression, result) -> None:
    assert parse(expression).eval().finalize() == result
