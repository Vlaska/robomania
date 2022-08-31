from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from robomania.utils import post_downloader

if TYPE_CHECKING:
    from .conftest import RawPostFactory, TRawPostFactory


@pytest.fixture
def get_posts(
    mocker: MockerFixture,
    raw_post_factory: TRawPostFactory,
    faker: Faker,
) -> list[RawPostFactory]:
    get_posts_mock = mocker.patch.object(post_downloader, 'get_posts')
    posts = raw_post_factory.bulk_create(5, faker)
    get_posts_mock.return_value = iter(posts)
    return posts


@pytest.mark.asyncio
async def test_download_posts(
    get_posts: list[RawPostFactory],
) -> None:
    posts = await post_downloader.PostDownloader.download_posts(
        'example', 3,
    )

    assert posts == get_posts
