from __future__ import annotations

import io
from datetime import datetime
from random import randint
from typing import cast

import PIL
import pytest
from disnake.ext.commands import Bot as DisBot  # type: ignore[attr-defined]
from faker import Faker
from mongomock_motor import AsyncMongoMockClient
from pytest import MonkeyPatch
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from robomania.cogs import announcements


class PostFactory:
    def __init__(self, fake: Faker) -> None:
        self.timestamp = fake.unix_time()
        self.post_text = fake.paragraphs(nb=10)
        self.post_id = fake.credit_card_number()
        self.post_url = fake.uri()
        self.likes = 15
        img_count = randint(1, 5)
        self.images_descriptions = fake.paragraphs(nb=img_count)
        self.images = [fake.image_url() for _ in range(img_count)]
        self.__dict__['with'] = []

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
        [[1024 * 9, 512], [1]],
        [[1024 * 9, 8000, 512], [1, 1]],
        [[100] * 12, [10, 2]],
        [[8000, 10, 500], [2, 1]],
        [[500, 7800, 200], [1, 2]],
    ]
)
def test_prepare_images(
    anno: announcements.Announcements,
    sizes: list[int],
    result: list[int],
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(announcements, 'MAX_TOTAL_SIZE_OF_IMAGES', 8 * 1024)
    bytesio_mock = mocker.Mock(spec=io.BytesIO)

    get_buffer_mock = bytesio_mock.getbuffer = mocker.Mock(spec=io.BytesIO)
    type(get_buffer_mock.return_value).nbytes = mocker.PropertyMock(
        side_effect=sizes
    )

    reduce_image_size_mock = mocker.patch.object(anno, 'reduce_image_size')
    reduce_image_size_mock.return_value = bytesio_mock

    out = list(anno.prepare_images([(bytesio_mock, 'test.png')] * sum(result)))
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


@pytest.mark.asyncio
async def test_get_only_new_posts(
    anno: announcements.Announcements,
    mocker: MockerFixture,
    faker: Faker,
) -> None:
    posts = PostFactory.bulk(faker, 12)

    sorted_posts = sorted(posts, key=lambda x: x.timestamp)
    newest_old_post = sorted_posts[5]

    async def _wrapper():
        return newest_old_post.timestamp

    mocker.patch.object(anno, 'get_latest_post_timestamp', _wrapper)

    newest_posts = await anno.get_only_new_posts(list(map(vars, posts)))

    assert newest_posts == list(map(vars, sorted_posts[6:]))


def test_filter_fields(
    anno: announcements.Announcements,
    faker: Faker,
) -> None:
    post = vars(PostFactory(faker))

    assert set(anno.filter_fields(post).keys()) == set(anno.fields_to_keep)


def test_change_image_format(
    anno: announcements.Announcements,
    faker: Faker,
) -> None:
    img = faker.image((1000, 1000), 'png')
    png_img = io.BytesIO(img)

    jpg_img = anno.change_image_format(png_img)
    jpg_img.seek(0)
    assert isinstance(jpg_img, io.BytesIO)
    assert jpg_img.read(4) == b'\xff\xd8\xff\xe0'


def test_change_image_resolution(
    anno: announcements.Announcements,
    faker: Faker,
) -> None:
    img = faker.image((1000, 1000), 'jpeg')
    og_img = io.BytesIO(img)

    resized_img = anno.reduce_image_resolution(og_img, 0.5)
    resized_img.seek(0)
    assert isinstance(resized_img, io.BytesIO)
    f = PIL.Image.open(resized_img)
    assert f.size == (500, 500)


@pytest.mark.parametrize('no_images', [False, True])
@pytest.mark.asyncio
async def test_send_announcements(
    anno: announcements.Announcements,
    mocker: MockerFixture,
    faker: Faker,
    no_images: bool,
) -> None:
    post = PostFactory(faker)
    if no_images:
        post.images.clear()

    format_announcement_text_mock = mocker.patch.object(
        anno,
        'format_announcement_text'
    )

    text_len = len(post.post_text)
    t = [
        f'{post.timestamp}{post.post_text[:text_len//2]}',
        f'{post.post_text[text_len//2:]}{post.post_url}',
    ]
    format_announcement_text_mock.return_value = t

    images = [faker.image((8, 8)) for _ in range(5)]
    prepared_images = [images[:2], images[2:4], images[4:]]

    download_images_mock = mocker.patch.object(anno, 'download_images')
    download_images_mock.return_value = images

    prepare_images_mock = mocker.patch.object(anno, 'prepare_images')
    prepare_images_mock.return_value = iter(prepared_images)

    send_announcements_mock = mocker.patch.object(anno, '_send_announcements')

    await anno.send_announcements(vars(post))

    format_announcement_text_mock.assert_called_once_with(
        post.post_text, post.timestamp, post.post_url
    )
    if no_images:
        download_images_mock.assert_not_called()
        prepare_images_mock.assert_not_called()
        send_announcements_arguments = [
            mocker.call(t[0]),
            mocker.call(t[1]),
        ]
    else:
        download_images_mock.assert_called_once_with(post.images)
        prepare_images_mock.assert_called_once_with(images)
        send_announcements_arguments = [
            mocker.call(t[0]),
            mocker.call(t[1], prepared_images[0]),
            mocker.call(None, prepared_images[1]),
            mocker.call(None, prepared_images[2]),
        ]

    send_announcements_mock.assert_called()
    assert send_announcements_mock.call_args_list == send_announcements_arguments


@pytest.mark.parametrize('new_posts', [False, True])
@pytest.mark.asyncio
async def test_check_for_announcements(
    anno: announcements.Announcements,
    faker: Faker,
    mocker: MockerFixture,
    new_posts: bool,
) -> None:
    posts = PostFactory.bulk(faker, 20)
    sorted_posts = sorted(posts, key=lambda x: x.timestamp)
    filtered_out_posts = sorted_posts[17:]

    download_facebook_posts_mock = mocker.patch.object(
        anno,
        'download_facebook_posts'
    )
    download_facebook_posts_mock.return_value = posts

    get_only_new_posts_mock = mocker.patch.object(anno, 'get_only_new_posts')
    filter_out_only_event_posts_mock = mocker.patch.object(
        anno, 'filter_out_only_event_posts'
    )

    if new_posts:
        filtered_posts = filtered_out_posts
    else:
        filtered_posts = []

    get_only_new_posts_mock.return_value = filtered_posts
    filter_out_only_event_posts_mock.return_value = filtered_posts

    send_announcements_mock = mocker.patch.object(anno, 'send_announcements')
    save_posts_mock = mocker.patch.object(anno, 'save_posts')

    await anno._check_for_announcements()

    download_facebook_posts_mock.assert_called_once()
    get_only_new_posts_mock.assert_called_once_with(posts)
    filter_out_only_event_posts_mock.assert_called_once_with(filtered_posts)

    if new_posts:
        assert send_announcements_mock.call_args_list == [
            mocker.call(filtered_out_posts[0]),
            mocker.call(filtered_out_posts[1]),
            mocker.call(filtered_out_posts[2]),
        ]
        save_posts_mock.assert_called_once_with(filtered_out_posts)
    else:
        send_announcements_mock.assert_not_called()
        save_posts_mock.assert_not_called()


@pytest.mark.parametrize('with_content,has_event', [
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
    has_event: bool,
) -> None:
    post = vars(PostFactory(faker))

    post['with'] = with_content

    assert anno._post_contains_event(post) is has_event


def test_filter_out_only_event_posts(
    anno: announcements.Announcements,
    faker: Faker,
) -> None:
    ps = p0, p1, p2, p3 = list(map(vars, PostFactory.bulk(faker, 4)))
    p0['post_text'] = ''

    p1['post_text'] = ''
    p1['with'].append({'name': 'event'})

    p2['with'].append({'name': 'event'})

    p3['with'].append({'name': 'not an event'})

    assert anno.filter_out_only_event_posts(ps) == [p0, p2, p3]
