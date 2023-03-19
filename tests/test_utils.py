from __future__ import annotations

import io
import logging

from pytest_mock import MockerFixture

from robomania import utils
from robomania.utils import pipe


def test_rewindable_buffer(mocker: MockerFixture) -> None:
    binary_buf = io.BytesIO(b"Lorem ipsum")
    text_buf = io.StringIO("Lorem ipsum")

    binary_spy = mocker.spy(binary_buf, "seek")
    text_spy = mocker.spy(text_buf, "seek")

    with utils.rewindable_buffer(binary_buf, text_buf) as (b1, b2):
        b1.read(-1)
        b2.read(-1)

    binary_spy.assert_called_once_with(0)
    text_spy.assert_called_once_with(0)
    assert binary_buf.tell() == 0
    assert text_buf.tell() == 0


def test_rewindable_buffer_preserve_order(mocker: MockerFixture) -> None:
    binary_buf = io.BytesIO(b"Lorem ipsum")
    text_buf = io.StringIO("Lorem ipsum")

    with utils.rewindable_buffer(binary_buf, text_buf) as (b1, b2):
        assert b1 is binary_buf
        assert b2 is text_buf


def test_preconfigure(mocker: MockerFixture) -> None:
    dummy_class = mocker.Mock()
    dummy_class.preconfigure = mocker.Mock()

    utils.preconfigure(dummy_class)
    dummy_class.preconfigure.assert_called_once()


def test_preconfigure_missing_method(caplog) -> None:
    class Dummy:
        pass

    with caplog.at_level(logging.WARNING, logger="robomania"):
        utils.preconfigure(Dummy)

    # assert 'Preconfiguration method missing' in caplog.records[-1].msg
    assert "Preconfiguration method missing" in caplog.text


class TestPipe:
    @staticmethod
    def f1(x):
        return x + 5

    @staticmethod
    def f2(x):
        return x - 3

    @staticmethod
    def f3(x):
        return x * 2

    @staticmethod
    def f4(x):
        return x**2

    @staticmethod
    def f5(x):
        return x / 4

    def test_adding_stages(self) -> None:
        p = pipe.Pipe(self.f1)
        p | self.f2 | self.f3
        p.add(self.f4)
        p = self.f5 | p

        assert p.pipeline == [self.f5, self.f1, self.f2, self.f3, self.f4]

    def test_run(self) -> None:
        p = pipe.Pipe(self.f1)
        p | self.f2 | self.f3
        p.add(self.f4)
        p = self.f5 | p

        assert p(20) == 196

    def test_copy(self) -> None:
        p1 = pipe.Pipe(self.f1)
        p2 = p1.copy()

        assert p1.pipeline == p2.pipeline

        p2.add(self.f2)

        assert p1.pipeline != p2.pipeline
