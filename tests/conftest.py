from __future__ import annotations

import asyncio
from datetime import datetime
from io import StringIO
from typing import Any

import pytest
from mongomock_motor import AsyncMongoMockClient

from robomania.config import Config

configuration = StringIO('''DEBUG=1''')


class _Bot:
    loop = asyncio.new_event_loop()
    config = Config
    Config.load_env('', stream=configuration)

    def __init__(self, client):
        self.client = client
        self.announcements_last_checked = datetime(2009, 4, 13, 12, 6, 10)

    def get_db(self, name: str) -> Any:
        return self.client[name]


@pytest.fixture
def bot(client) -> _Bot:
    return _Bot(client)


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("127.0.0.1", 1025)


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    return 413612


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> AsyncMongoMockClient:
    c = AsyncMongoMockClient()

    return c
