from __future__ import annotations

import asyncio
from datetime import datetime
from io import StringIO
from typing import Any, Self, Type

import pytest
from faker import Faker
from mongomock_motor import AsyncMongoMockClient

from robomania import config
from robomania.models.facebook_post import FacebookPostScraped

configuration = StringIO("""DEBUG=1""")


class FBPost:
    post_id = 413
    images: None = None
    is_event = False

    def __init__(self, faker: Faker) -> None:
        self.timestamp = faker.unix_time()
        self.post_text = faker.text(5000)
        self.post_url = faker.uri()


class _Bot:
    loop = asyncio.new_event_loop()
    settings = config.settings
    bot: _Bot

    def __init__(self, client):
        self.client = client
        self.__class__.bot = self

    def get_db(self, name: str) -> Any:
        return self.client[name]

    @classmethod
    def get_bot(cls) -> _Bot:
        return cls.bot

    def get_user(self, id: int):
        pass


class DummyFacebookPost(FacebookPostScraped):
    @classmethod
    def from_faker(cls, faker: Faker) -> Self:
        post_id = faker.credit_card_number()
        timestamp = faker.unix_time()
        text = faker.text(1500)
        url = faker.uri()
        was_posted = faker.pybool()

        post = {
            "post_id": post_id,
            "timestamp": timestamp,
            "publish_date": datetime.fromtimestamp(timestamp).isoformat(),
            "images": [],
            "scrambled_url": url,
            "url": url,
            "text": text,
            "was_posted": was_posted,
            "subpost": None,
        }

        return cls(**post)

    @classmethod
    def bulk_create(cls, num_of_posts: int, faker: Faker) -> list[Self]:
        return [cls.from_faker(faker) for _ in range(num_of_posts)]


TPostFactory = Type[DummyFacebookPost]


@pytest.fixture(scope="session")
def _set_settings():
    config.settings = config.BasicSettings(
        debug=True,
        announcements_target_channel=0,
        facebook_cookies_path="",
    )


@pytest.fixture()
def bot(client, _set_settings) -> _Bot:
    return _Bot(client)


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("127.0.0.1", 1025)


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    return 413612


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> AsyncMongoMockClient:
    c = AsyncMongoMockClient()

    return c


@pytest.fixture()
def post_factory() -> FacebookPostScraped:
    return DummyFacebookPost


@pytest.fixture()
def raw_post_factory() -> FacebookPostScraped:
    return FacebookPostScraped


@pytest.fixture()
def fb_post(post_factory: FacebookPostScraped, faker: Faker) -> DummyFacebookPost:
    return post_factory.from_faker(faker)
