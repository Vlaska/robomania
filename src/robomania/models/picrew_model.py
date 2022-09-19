from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, cast

import disnake
from attrs import asdict, define, field
from bson import ObjectId
from disnake import User
from pymongo.errors import WriteError

from robomania.bot import Robomania
from robomania.models.model import Model
from robomania.utils.exceptions import DuplicateError

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from pymongo.database import Database
    from pymongo.results import InsertOneResult


@define
class PicrewCountByPostStatus:
    posted: int
    not_posted: int

    @classmethod
    def from_mongo_documents(
        cls,
        documents: list[dict[str, int | bool]]
    ) -> PicrewCountByPostStatus:
        t = {
            'posted': 0,
            'not_posted': 0,
        }

        for i in documents:
            count = i['count']

            if i['posted']:
                t['posted'] = count
            else:
                t['not_posted'] = count

        return cls(**t)


@define
class PicrewModel(Model):
    user: User | None
    link: str
    add_date: datetime
    was_posted: bool
    id: ObjectId = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)

        if self.user:
            out['user'] = self.user.id

        id = out.pop('id', None)

        if id:
            out['_id'] = id

        return out

    @classmethod
    def from_raw(cls, post: dict[str, Any]) -> PicrewModel:
        post = post.copy()
        _id = post.pop('_id', None)

        return cls(
            id=_id,
            **post
        )

    async def save(self, db: Database) -> None:
        col = db.picrew
        document = self.to_dict()

        if self.id:
            await cast(
                Awaitable,
                col.update_one({'_id': self.id}, {'$set': document})
            )
        else:
            try:
                result: InsertOneResult = await cast(
                    Awaitable,
                    col.insert_one(document)
                )
            except WriteError as e:
                if e.code == 11000:
                    raise DuplicateError('Duplicate picrew link')
                raise e
            else:
                self.id = result.inserted_id

    @classmethod
    async def get(
        cls,
        db: AsyncIOMotorDatabase,
        pipeline: list[dict[str, Any]]
    ) -> list[PicrewModel]:
        col = db.picrew
        aggregator = col.aggregate(pipeline)
        bot = Robomania.get_bot()

        out = []

        async for i in aggregator:
            user_id = i['user']
            if (
                user_id is not None and
                (user := bot.get_user(user_id)) is None
            ):
                try:
                    user = await bot.fetch_user(i['user'])
                except disnake.NotFound:
                    user = None
            else:
                user = None

            i['user'] = user

            model = cls.from_raw(i)

            out.append(model)

        return out

    @classmethod
    async def get_random_unposted(
        cls,
        db: Database,
        count: int
    ) -> list[PicrewModel]:
        pipeline: list[dict] = [
            {'$match': {'was_posted': False}},
            {'$sample': {'size': count}}
        ]

        return await cls.get(db, pipeline)

    @classmethod
    async def count_posted_and_not_posted(
        cls,
        db: Database
    ) -> PicrewCountByPostStatus:
        pipeline = [
            {'$group': {'_id': '$was_posted', 'count': {'$sum': 1}}},
            {'$project': {'_id': 0, 'posted': '$_id', 'count': 1}}
        ]

        results = await cast(
            Awaitable, db.picrew.aggregate(pipeline)  # type: ignore
        ).to_list(None)

        return PicrewCountByPostStatus.from_mongo_documents(results)

    @staticmethod
    def create_collections(db: Database) -> None:
        import pymongo

        col = db.picrew
        col.create_index([('link', pymongo.TEXT)], unique=True)
