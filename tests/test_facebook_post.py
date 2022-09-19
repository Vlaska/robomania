from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from faker import Faker
from mongomock_motor import AsyncMongoMockClient, AsyncMongoMockDatabase
from pytest_mock import MockerFixture

from robomania.models.facebook_post import FacebookPost

if TYPE_CHECKING:
    from .conftest import TPostFactory, TRawPostFactory


@pytest.fixture
def dummy_post() -> dict:
    return {
        'timestamp': 0,
        'post_text': 'lorem ipsum',
        'post_id': 1,
        'post_url': 'https://example.org/post/1',
        'images': [],
    }


@pytest.fixture
def dummy_fb_post(dummy_post) -> FacebookPost:
    return FacebookPost.from_dict(dummy_post)


@pytest.mark.parametrize('post,result', [
    [[{'name': 'not event'}, {'name': 'event'}], True],
    [[{'name': 'not event'}, {'name': 'not event'}], False],
    [[{}], False],
])
def test__post_contains_event(post, result) -> None:
    t = {'with': post}
    assert FacebookPost._post_contains_event(t) is result


@pytest.mark.parametrize('post_with,is_event,result', [
    [None, None, False],
    [None, False, False],
    [None, True, True],
    [[], False, False],
    [[{'name': 'event'}], None, True],
    [[{'name': 'event'}], False, False],
    [[{'name': 'not event'}], False, False],
])
def test_create_post(dummy_post: dict, post_with, is_event, result) -> None:
    post = dummy_post.copy()
    post['with'] = post_with

    if is_event is not None:
        post['is_event'] = is_event

    assert FacebookPost(**dummy_post, post=post).is_event is result


def test_from_dict(dummy_post: dict) -> None:
    dummy_post['is_event'] = True

    result = FacebookPost.from_dict(dummy_post)

    assert result.is_event
    assert result.post_id == dummy_post['post_id']
    assert result.post_text == dummy_post['post_text']
    assert result.post_url == dummy_post['post_url']
    assert result.timestamp == dummy_post['timestamp']
    assert not result.images


def test_to_dict(dummy_fb_post: FacebookPost, dummy_post: dict) -> None:
    dummy_post.update({
        'is_event': False
    })
    assert dummy_fb_post.to_dict() == dummy_post


@pytest.mark.asyncio
async def test_save(
    dummy_fb_post: FacebookPost, client: AsyncMongoMockClient
) -> None:
    db: AsyncMongoMockDatabase = client.robomania

    tmp = await db.posts.find({'post_id': dummy_fb_post.post_id}).to_list()
    assert not tmp

    await FacebookPost.save(db, [dummy_fb_post])

    tmp = await db.posts.find({'post_id': dummy_fb_post.post_id}).to_list()
    assert tmp


@pytest.mark.asyncio
async def test_latest_timestamp(
    faker: Faker,
    post_factory: TPostFactory,
    client: AsyncMongoMockClient
) -> None:
    collection = client.robomania.posts

    posts = post_factory.bulk_create(50, faker)

    latest_timestamp = int(datetime.now().timestamp()) + 60

    known_post = post_factory.from_faker(faker)
    known_post.timestamp = latest_timestamp

    posts.append(known_post)
    await collection.insert_many(vars(i) for i in posts)

    assert await \
        FacebookPost.latest_timestamp(client.robomania) == latest_timestamp


@pytest.mark.asyncio
async def test_latest_timestamp_no_posts(
    client: AsyncMongoMockClient,
) -> None:
    assert await FacebookPost.latest_timestamp(client.robomania) == 0


def test_from_raw(dummy_post: dict) -> None:
    dummy_post.update({
        'with': [{'name': 'not event'}],
        'post_images': [],
        'images_low_res': [],
    })

    FacebookPost.from_raw(dummy_post)


@pytest.mark.asyncio
async def test_get_only_new_posts(
    mocker: MockerFixture,
    faker: Faker,
    raw_post_factory: TRawPostFactory
) -> None:
    posts: list[FacebookPost] = raw_post_factory.bulk_create(12, faker)

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


def test_event_posts(
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

    assert all(
        i.timestamp == j['timestamp']
        for i, j in zip(
            FacebookPost.remove_event_posts(pr), [p0, p2, p3]
        )
    )
