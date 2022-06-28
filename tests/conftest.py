from __future__ import annotations
from datetime import datetime
from typing import Any

import pytest
import asyncio
from mongomock_motor import AsyncMongoMockClient


class _Bot:
    loop = asyncio.new_event_loop()

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
