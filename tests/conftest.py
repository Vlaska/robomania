from __future__ import annotations

import pytest
import asyncio
from mongomock_motor import AsyncMongoMockClient


class _Bot:
    loop = asyncio.new_event_loop()


@pytest.fixture
def bot() -> _Bot:
    return _Bot()


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("127.0.0.1", 1025)


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    return 413612


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> AsyncMongoMockClient:
    c = AsyncMongoMockClient()

    monkeypatch.setattr('robomania.cogs.utils.get_client', lambda: c)

    return c
