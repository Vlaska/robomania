from __future__ import annotations

import io
from datetime import datetime
from typing import TYPE_CHECKING, cast

import PIL
import pytest
from disnake.ext.commands import Bot as DisBot  # type: ignore[attr-defined]
from faker import Faker
from pytest import MonkeyPatch
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from robomania.cogs import announcements
from robomania.types import announcement_post, image
from robomania.types.facebook_post import FacebookPost

if TYPE_CHECKING:
    from .conftest import TPostFactory, TRawPostFactory


@pytest.fixture
def anno(bot: object, mocker: MockerFixture) -> announcements.Announcements:
    a = announcements.Announcements
    mocker.patch.object(a.check_for_announcements, 'start')
    mocker.patch.object(a.check_for_announcements, '_before_loop')
    a._DISABLE_ANNOUNCEMENTS_LOOP = True

    return a(cast(DisBot, bot))


@pytest.mark.parametrize(
    'now,result', [
        [datetime(1, 1, 1), False],
        [datetime(2009, 4, 13, 12, 10), False],
        [datetime(2009, 4, 13, 12), False],
        [datetime(2009, 4, 13, 12, 40), True],
        [datetime(2009, 4, 13, 12, 39, 59), True],
        [datetime(2021, 1, 1), True],
    ],
)
def test_enough_time_from_last_check(
    anno: announcements.Announcements,
    now: datetime,
    result: bool,
    mocker: MockerFixture,
) -> None:
    datetime_mock = mocker.patch('datetime.datetime')
    datetime_mock.now.return_value = now

    assert anno.enough_time_from_last_check() is result


@pytest.mark.asyncio
async def test_download_images(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request('/test/image/example.png').respond_with_data(
        b'OK'
    )
    httpserver.expect_request('/test/emote/kek.jpg').respond_with_data(
        b'KO'
    )

    print([
        httpserver.url_for('/test/image/example.png'),
        httpserver.url_for('/test/emote/kek.jpg'),
    ])

    images = await image.DiscordImage.download_images([
        httpserver.url_for('/test/image/example.png'),
        httpserver.url_for('/test/emote/kek.jpg'),
    ])

    assert images[0].image.read() == b'OK'
    assert images[0].name == 'example.png'
    assert images[1].image.read() == b'KO'
    assert images[1].name == 'kek.jpg'


@pytest.mark.parametrize(
    'sizes,result',
    [
        [[1024, 6000], [2]],
        [[[1024 * 9, 512]], [1]],
        [[[1024 * 9, 8000], 512], [1, 1]],
        [[100] * 12, [10, 2]],
        [[8000, 10, 500], [2, 1]],
        [[500, 7800, 200], [1, 2]],
    ]
)
def test_prepare_images(
    sizes: list[int | list[int]],
    result: list[int],
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(image, 'MAX_TOTAL_SIZE_OF_IMAGES', 8 * 1024)
    bytesio_mock = mocker.Mock(spec=io.BytesIO)

    class MockDiscordPostImage(image.DiscordImage):
        image = bytesio_mock
        name = 'lorem ipsum'

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


def test_format_announcements_date(fb_post: TPostFactory) -> None:
    t = announcement_post.AnnouncementPost(fb_post)

    assert f'<t:{fb_post.timestamp}:F>' in t.announcements_date


def test_format_announcement_text(
    fb_post: TPostFactory
) -> None:
    anno = announcement_post.AnnouncementPost(fb_post, None)

    formatted_text = anno.format_text(fb_post.post_text)

    assert all(len(i) <= 2000 for i in formatted_text)


def test_change_image_format(
    faker: Faker,
) -> None:
    img_raw = faker.image((1000, 1000), 'png')
    png_img = io.BytesIO(img_raw)
    img = image.DiscordImage(png_img, '')

    img._change_image_format()

    assert isinstance(img.image, io.BytesIO)
    assert img._data.read(8) == b'\x89PNG\r\n\x1a\n'
    assert img.image.read(4) == b'\xff\xd8\xff\xe0'


def test_change_image_resolution(
    faker: Faker,
) -> None:
    og_img = faker.image((1000, 1000), 'jpeg')
    img = image.DiscordImage(io.BytesIO(og_img), '')

    img._reduce_image_resolution(0.5)
    assert isinstance(img.image, io.BytesIO)
    f = PIL.Image.open(img.image)
    assert f.size == (500, 500)


@pytest.mark.parametrize('with_content,is_event', [
    [
        [
            {'name': 'event',
             'link': '/events/542918700556684?locale2=en_US&__tn__=C-R'}
        ],
        True
    ],
    [
        [
            {'name': 'Prideshop.pl',
             'link': '/prideshoppl/?locale2=en_US&__tn__=CH-R'},
            {'name': 'event',
                'link': '/events/542918700556684?locale2=en_US&__tn__=C-R'}
        ],
        True
    ],
    [
        [
            {'name': 'Prideshop.pl',
             'link': '/prideshoppl/?locale2=en_US&__tn__=CH-R'}
        ],
        False
    ]
])
def test_post_contains_event(
    raw_post_factory: TRawPostFactory,
    faker: Faker,
    with_content: list[dict[str, str]],
    is_event: bool,
) -> None:
    post = raw_post_factory(faker)

    post['with'] = with_content

    assert FacebookPost.from_raw(post).is_event is is_event


def test_filter_out_only_event_posts(
    anno: announcements.Announcements,
    faker: Faker,
    raw_post_factory: TRawPostFactory,
) -> None:
    ps = p0, p1, p2, p3 = raw_post_factory.bulk_create(4, faker)
    p0['post_text'] = ''

    p1['post_text'] = ''
    p1['with'].append({'name': 'event'})

    p2['with'].append({'name': 'event'})

    p3['with'].append({'name': 'not an event'})

    pr = [FacebookPost.from_raw(i) for i in ps]

    # assert anno.filter_out_only_event_posts(pr) == [p0, p2, p3]
    assert all(i.timestamp == j['timestamp'] for i, j in zip(
        anno.filter_out_only_event_posts(pr), [p0, p2, p3]))
