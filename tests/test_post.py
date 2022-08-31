from __future__ import annotations

import pytest
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

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


@pytest.mark.asyncio
async def test_get_images_images_on_input(mocker: MockerFixture) -> None:
    dl = mocker.patch.object(post.Image, 'download_images')
    image_mock = mocker.Mock(spec=post.Image)

    images = [image_mock] * 3

    res = await post.Post._get_images(images)

    dl.assert_not_called()
    assert res is images


@pytest.mark.asyncio
async def test_get_images_links_on_input(mocker: MockerFixture) -> None:
    dl = mocker.patch.object(post.Image, 'download_images')
    downloaded_images = [object()]
    dl.return_value = downloaded_images

    links = ['https://example.org/img.png'] * 3

    res = await post.Post._get_images(links)

    dl.assert_called_once_with(links)
    assert res is downloaded_images


@pytest.mark.asyncio
async def test_prepare_images_no_images() -> None:
    p = post.Post('')

    assert (await p._prepare_images()) == (None, None)


@pytest.mark.asyncio
async def test_prepare_images(mocker: MockerFixture) -> None:
    images = [object() for _ in range(4)]

    get_images_mock = mocker.patch.object(post.Post, '_get_images')
    get_images_mock.return_value = images

    prepare_images_mock = mocker.patch.object(post.Image, 'prepare_images')
    prepare_images_mock.return_value = iter(images)

    p = post.Post('', images)
    first, iterator = await p._prepare_images()

    get_images_mock.assert_called_once_with(images)
    prepare_images_mock.assert_called_once_with(images)
    assert first is images[0]
    assert all(i is j for i, j in zip(iterator, images[1:]))
