from __future__ import annotations

from typing import cast

from pymongo.database import Database

from robomania.bot import Robomania
from robomania.models.model import CollectionSetup
from robomania.models.picrew_model import PicrewModel

models = [
    PicrewModel,
]


__all__ = [i.__name__ for i in models]


def create_collections() -> None:
    bot = Robomania.get_bot()
    with bot.blocking_db():
        db = cast(Database, bot.get_db("robomania"))

        for i in models:
            if isinstance(i, CollectionSetup):
                i.create_collections(db)
