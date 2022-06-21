from __future__ import annotations

import io
from datetime import datetime
from typing import cast

import pytest
from robomania.cogs import announcements, utils
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from disnake.ext.commands import Bot as DisBot
from pytest_httpserver import HTTPServer


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
        [[1024 * 9], [1]],
        [[1024 * 9, 512], [1, 1]],
        [[100] * 12, [10, 2]],
        [[8000, 10, 100], [2, 1]],
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
    type(get_buffer_mock.return_value).nbytes = mocker.PropertyMock(side_effect=sizes)

    out = list(anno.prepare_images([(bytesio_mock, 'test.png')] * len(sizes)))
    print(out)
    assert list(map(len, out)) == result


@pytest.mark.skip
def test_format_announcements_date(
    anno: announcements.Announcements
) -> None:
    pass


@pytest.mark.skip
def test_format_posts_url(
    anno: announcements.Announcements
) -> None:
    pass


@pytest.mark.skip
def test_format_announcement_text(
    anno: announcements.Announcements
) -> None:
    pass


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_latest_post_timestamp() -> None:
    pass


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
def test_split_text(
    anno: announcements.Announcements
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
