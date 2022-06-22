from __future__ import annotations

import pytest
import asyncio


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
