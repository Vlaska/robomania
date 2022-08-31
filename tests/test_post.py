from __future__ import annotations

from pytest import MonkeyPatch

from robomania.types import post


def test_process_text() -> None:
    text = '  Lorem  Ipsum... -+  abc .*abc*  '

    t = post.Post(text)

    assert t.text == r'Lorem Ipsum…-+ abc.\*abc\*'


def test_long_text_wrapping(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(post.Post.wrapper, 'width', 50)
    monkeypatch.setattr(post, 'MAX_CHARACTERS_PER_POST', 50)

    text = (
        'Sit sunt culpa duis enim occaecat anim eiusmod proident nulla. '
        'Qui labore do id anim deserunt amet occaecat. Sint irure mollit '
        'Lorem excepteur ea ex fugiat.'
    )

    p = post.Post(text)
    assert p.wrapped_text == [
        'Sit sunt culpa duis enim occaecat anim eiusmod',
        'proident nulla. Qui labore do id anim deserunt',
        'amet occaecat. Sint irure mollit Lorem excepteur',
        'ea ex fugiat.'
    ]


def test_short_text_wrapping() -> None:
    text = 'Duis quis consectetur sunt culpa.'

    p = post.Post(text)

    assert p.wrapped_text == [text]
