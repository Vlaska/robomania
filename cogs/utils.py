from __future__ import annotations

from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

announcements_last_checked = datetime(1, 1, 1)


client: AsyncIOMotorClient
is_initialized = False


def get_db(name: str) -> Database:
    return get_client()[name]


def get_client() -> AsyncIOMotorClient:
    try:
        return client
    except NameError:
        raise ValueError('Trying to import database before its initialized.')


def init_db() -> None:
    global client
    global is_initialized

    if is_initialized:
        return

    is_initialized = True

    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')

    port = os.getenv('DB_PORT', '')
    auth_db = os.getenv('DB_AUTH_DB', '')

    if port:
        port = f':{port}'
    
    if auth_db:
        auth_db = f'{auth_db}/'

    client = AsyncIOMotorClient(
        f"mongodb+srv://{username}:{password}@{host}{port}/{auth_db}?retryWrites=true&w=majority"
    )
