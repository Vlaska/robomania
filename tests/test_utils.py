from __future__ import annotations

import io
import logging

from pytest_mock import MockerFixture

from robomania import utils


def test_rewindable_buffer(mocker: MockerFixture) -> None:
    binary_buf = io.BytesIO(b'Lorem ipsum')
    text_buf = io.StringIO('Lorem ipsum')

    binary_spy = mocker.spy(binary_buf, 'seek')
    text_spy = mocker.spy(text_buf, 'seek')

    with utils.rewindable_buffer(binary_buf, text_buf) as (b1, b2):
        b1.read(-1)
        b2.read(-1)

    binary_spy.assert_called_once_with(0)
    text_spy.assert_called_once_with(0)
    assert binary_buf.tell() == 0
    assert text_buf.tell() == 0


def test_rewindable_buffer_preserve_order(mocker: MockerFixture) -> None:
    binary_buf = io.BytesIO(b'Lorem ipsum')
    text_buf = io.StringIO('Lorem ipsum')

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

    with caplog.at_level(logging.WARNING, logger='robomania'):
        utils.preconfigure(Dummy)

    # assert 'Preconfiguration method missing' in caplog.records[-1].msg
    assert 'Preconfiguration method missing' in caplog.text
