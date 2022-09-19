from __future__ import annotations

from robomania.bot import Robomania
from robomania.models.facebook_post import FacebookPost
from robomania.models.model import CollectionSetup
from robomania.models.picrew_model import PicrewModel

models = [
    FacebookPost,
    PicrewModel,
]


__all__ = [i.__name__ for i in models]


def create_collections() -> None:
    bot = Robomania.get_bot()
    with bot.blocking_db():
        db = bot.get_db('robomania')

        for i in models:
            if isinstance(i, CollectionSetup):
                i.create_collections(db)
