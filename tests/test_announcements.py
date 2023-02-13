from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from disnake.ext.commands import Bot as DisBot  # type: ignore[attr-defined]
from faker import Faker
from pytest_mock import MockerFixture

from robomania.cogs import announcements
from robomania.models.facebook_post import FacebookPost
from robomania.types import announcement_post

if TYPE_CHECKING:
    from .conftest import TPostFactory, TRawPostFactory


@pytest.fixture
def anno(bot: object, mocker: MockerFixture) -> announcements.Announcements:
    a = announcements.Announcements
    mocker.patch.object(a.check_for_announcements, 'start')
    mocker.patch.object(a.check_for_announcements, '_before_loop')
    a._DISABLE_ANNOUNCEMENTS_LOOP = True

    return a(cast(DisBot, bot))


# @pytest.mark.parametrize(
#     'now,result', [
#         [datetime(1, 1, 1), False],
#         [datetime(2009, 4, 13, 12, 10), False],
#         [datetime(2009, 4, 13, 12), False],
#         [datetime(2009, 4, 13, 12, 40), True],
#         [datetime(2009, 4, 13, 12, 39, 59), True],
#         [datetime(2021, 1, 1), True],
#     ],
# )
# def test_enough_time_from_last_check(
#     anno: announcements.Announcements,
#     now: datetime,
#     result: bool,
#     mocker: MockerFixture,
# ) -> None:
#     datetime_mock = mocker.patch('datetime.datetime')
#     datetime_mock.now.return_value = now

#     assert anno.enough_time_from_last_check() is result


def test_format_announcements_date(fb_post: TPostFactory) -> None:
    t = announcement_post.AnnouncementPost(fb_post)

    assert f'<t:{fb_post.timestamp}:F>' in t.announcements_date


def test_format_announcement_text(
    fb_post: TPostFactory
) -> None:
    anno = announcement_post.AnnouncementPost(fb_post, None)

    formatted_text = anno.format_text(fb_post.post_text)

    assert all(len(i) <= 2000 for i in formatted_text)


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
