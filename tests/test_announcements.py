from __future__ import annotations

import io
from datetime import datetime
from random import randint
from typing import cast

import pytest
from robomania.cogs import announcements, utils
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from disnake.ext.commands import Bot as DisBot  # type: ignore[attr-defined]
from pytest_httpserver import HTTPServer
from faker import Faker
from mongomock_motor import AsyncMongoMockClient


class PostFactory:
    def __init__(self, fake: Faker) -> None:
        self.timestamp = fake.unix_time()
        self.text = fake.paragraphs(nb=10)
        self.post_id = fake.credit_card_number()
        self.post_url = fake.uri()
        self.likes = 15
        img_count = randint(0, 5)
        self.images_descriptions = fake.paragraphs(nb=img_count)
        self.images = [fake.image_url() for _ in range(img_count)]

    @classmethod
    def bulk(cls, fake: Faker, num: int) -> list[PostFactory]:
        return [cls(fake) for _ in range(num)]


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
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils,
        'announcements_last_checked',
        datetime(2009, 4, 13, 12, 6, 10)
    )
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

    images = await anno.download_images([
        httpserver.url_for('/test/image/example.png'),
        httpserver.url_for('/test/emote/kek.jpg'),
    ])

    assert images[0][0].read() == b'OK'
    assert images[0][1] == 'example.png'
    assert images[1][0].read() == b'KO'
    assert images[1][1] == 'kek.jpg'


@pytest.mark.parametrize(
    'sizes,result',
    [
        [[1024, 6000], [2]],
        pytest.param(
            [1024 * 9], [1],
            marks=[pytest.mark.xfail(reason='not implemented')]
        ),
        pytest.param(
            [1024 * 9, 512], [1, 1],
            marks=[pytest.mark.xfail(reason='not implemented')]
        ),
        [[100] * 12, [10, 2]],
        [[8000, 10, 500], [2, 1]],
        [[500, 7800, 200], [1, 2]],
    ]
)
def test_prepare_images(
    anno: announcements.Announcements,
    sizes: list[int],
    result: list[int] | None,
    mocker: MockerFixture,
) -> None:
    bytesio_mock = mocker.Mock(spec=io.BytesIO)

    get_buffer_mock = bytesio_mock.getbuffer = mocker.Mock(spec=io.BytesIO)
    type(get_buffer_mock.return_value).nbytes = mocker.PropertyMock(
        side_effect=sizes
    )

    out = list(anno.prepare_images([(bytesio_mock, 'test.png')] * len(sizes)))
    print(out)
    assert list(map(len, out)) == result


def test_format_announcements_date(
    anno: announcements.Announcements
) -> None:
    timestamp = int(datetime.now().timestamp())
    assert f'<t:{timestamp}:F>' in anno.format_announcements_date(timestamp)


def test_format_announcement_text(
    anno: announcements.Announcements,
    faker: Faker,
) -> None:
    text = faker.text(5000)

    formatted_text = anno.format_announcement_text(
        text, faker.unix_time(), faker.uri()
    )

    assert all(len(i) <= 2000 for i in formatted_text)


@pytest.mark.asyncio
async def test_get_latest_post_timestamp(
    anno: announcements.Announcements,
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

    assert await anno.get_latest_post_timestamp() == latest_timestamp


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_only_new_posts(
    anno: announcements.Announcements
) -> None:
    pass


@pytest.mark.skip
def test_filter_fields(
    anno: announcements.Announcements
) -> None:
    pass


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_announcements(
    anno: announcements.Announcements,
) -> None:
    pass


@pytest.mark.skip
@pytest.mark.asyncio
async def test_check_for_announcements(
    anno: announcements.Announcements
) -> None:
    pass


@pytest.mark.skip
def test_in_allowed_time_range(
    anno: announcements.Announcements
) -> None:
    pass
