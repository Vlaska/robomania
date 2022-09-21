from __future__ import annotations

import asyncio
from datetime import datetime
from io import StringIO
from random import randint
from typing import Any, Type

import pytest
from faker import Faker
from mongomock_motor import AsyncMongoMockClient

from robomania.config import Config
from robomania.models.facebook_post import FacebookPost, TFacebookPost

configuration = StringIO('''DEBUG=1''')


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
    config = Config
    Config.load_env('', stream=configuration)
    bot: _Bot

    def __init__(self, client):
        self.client = client
        self.announcements_last_checked = datetime(2009, 4, 13, 12, 6, 10)
        self.__class__.bot = self

    def get_db(self, name: str) -> Any:
        return self.client[name]

    @classmethod
    def get_bot(cls) -> _Bot:
        return cls.bot

    def get_user(self, id: int):
        pass


class RawPostFactory(dict):
    def __init__(self, fake: Faker) -> None:
        self.timestamp = fake.unix_time()
        self.post_text = fake.text(1500)
        self.post_id = fake.credit_card_number()
        self.post_url = fake.uri()
        self.likes = 15
        img_count = randint(1, 5)
        self.images_descriptions = fake.paragraphs(nb=img_count)
        self.images = [fake.image_url() for _ in range(img_count)]
        self['with'] = []

    @classmethod
    def bulk_create(
        cls,
        num_of_posts: int,
        faker: Faker
    ) -> list[RawPostFactory]:
        return [cls(faker) for _ in range(num_of_posts)]

    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value
        self.__dict__[__name] = __value


class DummyFacebookPost(FacebookPost):
    @classmethod
    def from_faker(cls, faker: Faker, is_event: bool = False) -> TFacebookPost:
        post = {
            'timestamp': faker.unix_time(),
            'post_text': faker.text(1500),
            'post_id': faker.credit_card_number(),
            'post_url': faker.uri(),
            'images': [],
            'is_event': is_event,
        }

        return cls.from_dict(post)

    @classmethod
    def bulk_create(
        cls,
        num_of_posts: int,
        faker: Faker
    ) -> list[TFacebookPost]:
        return [cls.from_faker(faker) for _ in range(num_of_posts)]


TPostFactory = Type[DummyFacebookPost]
TRawPostFactory = Type[RawPostFactory]


@pytest.fixture
def bot(client) -> _Bot:
    return _Bot(client)


@pytest.fixture(scope='session')
def httpserver_listen_address():
    return ('127.0.0.1', 1025)


@pytest.fixture(scope='session', autouse=True)
def faker_seed():
    return 413612


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> AsyncMongoMockClient:
    c = AsyncMongoMockClient()

    return c


@pytest.fixture
def post_factory() -> TPostFactory:
    return DummyFacebookPost


@pytest.fixture
def raw_post_factory() -> TRawPostFactory:
    return RawPostFactory


@pytest.fixture
def fb_post(post_factory: TPostFactory, faker: Faker) -> DummyFacebookPost:
    return post_factory.from_faker(faker)
