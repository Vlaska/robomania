from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, cast

from attrs import asdict, define, field
from bson import ObjectId
from disnake import User

from robomania.bot import Robomania
from robomania.types.model import Model

if TYPE_CHECKING:
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
    user: User
    link: str
    add_date: datetime
    was_posted: bool
    id: ObjectId = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out['user'] = self.user.id
        id = out.pop('id', None)

        if id:
            out['_id'] = id

        return out

    @classmethod
    def from_raw(cls, post: dict[str, Any]) -> PicrewModel:
        bot = Robomania.get_bot()

        post = post.copy()
        _id = post.pop('_id', None)

        user_id = post.pop('user')
        user = bot.get_user(user_id)

        return cls(
            user=user,
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
            result: InsertOneResult = await cast(
                Awaitable,
                col.insert_one(document)
            )
            self.id = result.inserted_id

    @classmethod
    async def get_random_unposted(
        cls,
        db: Database,
        count: int
    ) -> list[PicrewModel]:
        col = db.picrew

        out = await cast(Awaitable, col.aggregate([  # type: ignore
            {'$match': {'was_posted': False}},
            {'$sample': {'size': count}}
        ])).to_list(count)

        return list(map(cls.from_raw, out))

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
