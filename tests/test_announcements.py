from __future__ import annotations

import io
from datetime import datetime
from random import randint
from typing import Any, cast

import PIL
import pytest
from disnake.ext.commands import Bot as DisBot  # type: ignore[attr-defined]
from faker import Faker
from mongomock_motor import AsyncMongoMockClient
from pytest import MonkeyPatch
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from robomania.cogs import announcements
from robomania.types import announcement_post, image
from robomania.types.facebook_post import FacebookPost


class PostFactory(dict):
    def __init__(self, fake: Faker) -> None:
        self.timestamp = fake.unix_time()
        self.post_text = fake.paragraphs(nb=10)
        self.post_id = fake.credit_card_number()
        self.post_url = fake.uri()
        self.likes = 15
        img_count = randint(1, 5)
        self.images_descriptions = fake.paragraphs(nb=img_count)
        self.images = [fake.image_url() for _ in range(img_count)]
        self['with'] = []

    @classmethod
    def bulk(cls, fake: Faker, num: int) -> list[PostFactory]:
        return [cls(fake) for _ in range(num)]

    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value
        self.__dict__[__name] = __value


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
    anno: announcements.Announcements,
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


def test_format_announcements_date(fb_post) -> None:
    t = announcement_post.AnnouncementPost(fb_post)

    assert f'<t:{fb_post.timestamp}:F>' in t.announcements_date


def test_format_announcement_text(
    fb_post
) -> None:
    anno = announcement_post.AnnouncementPost(fb_post, None)

    formatted_text = anno.format_text(fb_post.post_text)

    assert all(len(i) <= 2000 for i in formatted_text)


@pytest.mark.asyncio
async def test_get_latest_post_timestamp(
    faker: Faker,
    client: AsyncMongoMockClient
) -> None:
    collection = client.robomania.posts

    posts = PostFactory.bulk(faker, 50)

    latest_timestamp = int(datetime.now().timestamp()) + 60

    known_post = PostFactory(faker)
    known_post.timestamp = latest_timestamp

    posts.append(known_post)
    await collection.insert_many(vars(i) for i in posts)

    assert await \
        FacebookPost.latest_timestamp(client.robomania) == latest_timestamp


@pytest.mark.asyncio
async def test_get_only_new_posts(
    mocker: MockerFixture,
    faker: Faker,
) -> None:
    posts = PostFactory.bulk(faker, 12)

    sorted_posts = sorted(posts, key=lambda x: x.timestamp)
    newest_old_post = sorted_posts[5]

    async def _wrapper(_):
        return newest_old_post.timestamp

    mocker.patch.object(FacebookPost, 'latest_timestamp', _wrapper)

    newest_posts = await FacebookPost.get_only_new_posts(
        None,
        list(map(FacebookPost.from_raw, posts))
    )

    assert all(
        i['timestamp'] == j.timestamp
        for i, j in zip(map(vars, sorted_posts[6:]), newest_posts)
    )


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
    anno: announcements.Announcements,
    faker: Faker,
    with_content: list[dict[str, str]],
    is_event: bool,
) -> None:
    post = PostFactory(faker)

    post['with'] = with_content

    assert FacebookPost.from_raw(post).is_event is is_event


def test_filter_out_only_event_posts(
    anno: announcements.Announcements,
    faker: Faker,
) -> None:
    ps = p0, p1, p2, p3 = list(PostFactory.bulk(faker, 4))
    p0['post_text'] = ''

    p1['post_text'] = ''
    p1['with'].append({'name': 'event'})

    p2['with'].append({'name': 'event'})

    p3['with'].append({'name': 'not an event'})

    pr = [FacebookPost.from_raw(i) for i in ps]

    # assert anno.filter_out_only_event_posts(pr) == [p0, p2, p3]
    assert all(i.timestamp == j['timestamp'] for i, j in zip(
        anno.filter_out_only_event_posts(pr), [p0, p2, p3]))
