from __future__ import annotations

import io
from typing import cast

import PIL
import pytest
from faker import Faker
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from robomania.types import image


@pytest.fixture()
def img(faker: Faker) -> image.Image:
    img_raw = faker.image((1000, 1000), "png")
    img = image.Image(io.BytesIO(img_raw), "test.png")

    return img


@pytest.mark.asyncio()
async def test_download_images(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/test/image/example.png").respond_with_data(b"OK")
    httpserver.expect_request("/test/emote/kek.jpg").respond_with_data(b"KO")

    print(
        [
            httpserver.url_for("/test/image/example.png"),
            httpserver.url_for("/test/emote/kek.jpg"),
        ]
    )

    images = await image.Image.download_images(
        [
            httpserver.url_for("/test/image/example.png"),
            httpserver.url_for("/test/emote/kek.jpg"),
        ]
    )

    assert images[0].image.read() == b"OK"
    assert images[0].name == "example.png"
    assert images[1].image.read() == b"KO"
    assert images[1].name == "kek.jpg"


def test_change_image_format(img: image.Image) -> None:
    img._change_image_format()

    assert isinstance(img.image, io.BytesIO)
    assert img._data.read(8) == b"\x89PNG\r\n\x1a\n"
    assert img.image.read(4) == b"\xff\xd8\xff\xe0"


@pytest.mark.xfail(reason="Not implemented")
def test_change_image_format_changes_format_in_name(img: image.Image) -> None:
    img._change_image_format()

    assert img.name == "test.jpg"


@pytest.mark.parametrize(
    ("sizes", "result"),
    [
        ([1024, 6000], [2]),
        ([[1024 * 9, 512]], [1]),
        ([[1024 * 9, 8000], 512], [1, 1]),
        ([100] * 12, [10, 2]),
        ([8000, 10, 500], [2, 1]),
        ([500, 7800, 200], [1, 2]),
    ],
)
def test_prepare_images(
    sizes: list[int | list[int]],
    result: list[int],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(image, "MAX_TOTAL_SIZE_OF_IMAGES", 8 * 1024)
    bytesio_mock = mocker.Mock(spec=io.BytesIO)

    class MockDiscordPostImage(image.Image):
        image = bytesio_mock
        name = "lorem ipsum"

        def __init__(self, size: int | list[int]) -> None:
            self.reduced_size = False

            if isinstance(size, int):
                self._size = [size, size]
                self.dont_change_size = True
            else:
                self._size = size
                self.dont_change_size = False

        def reduce_size(self, max_size: int) -> None:
            assert not self.dont_change_size
            self.reduced_size = True

        @property
        def size(self) -> int:
            return cast(list[int], self._size)[self.reduced_size]

    images = list(map(MockDiscordPostImage, sizes))
    image_split = list(map(len, MockDiscordPostImage.prepare_images(images)))
    assert image_split == result


def test_change_image_resolution(
    faker: Faker,
) -> None:
    og_img = faker.image((1000, 1000), "jpeg")
    img = image.Image(io.BytesIO(og_img), "")

    img._reduce_image_resolution(0.5)
    assert isinstance(img.image, io.BytesIO)
    f = PIL.Image.open(img.image)
    assert f.size == (500, 500)


def test_reduce_size(faker: Faker, mocker: MockerFixture) -> None:
    img_raw = faker.image((7500, 7500), "tiff")
    change_format = mocker.spy(image.Image, "_change_image_format")
    reduce_resolution = mocker.spy(image.Image, "_reduce_image_resolution")

    img = image.Image(io.BytesIO(img_raw), "test.tiff")

    img.reduce_size(153600)

    assert img.size <= 153600
    change_format.assert_called_once()
    reduce_resolution.assert_called()


def test_reduce_size_cannot_reduce_enough(mocker: MockerFixture) -> None:
    img_raw = mocker.Mock(io.BytesIO)
    mocker.patch.object(
        image.Image, "size", new_callable=mocker.PropertyMock(return_value=10000)
    )
    mocker.patch.object(image.Image, "_reduce_image_resolution")
    mocker.patch.object(image.Image, "_change_image_format")

    img = image.Image(img_raw, "test.png")

    with pytest.raises(ValueError, match="below given size"):
        img.reduce_size(100)
