from __future__ import annotations

from collections.abc import Awaitable, Coroutine, Mapping
from typing import TYPE_CHECKING, Any, Protocol, cast

import disnake
from attrs import asdict, define, field
from pymongo.errors import WriteError

from robomania.bot import Robomania
from robomania.models.model import Model
from robomania.utils.exceptions import DuplicateError

if TYPE_CHECKING:
    from datetime import datetime

    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from pymongo.database import Database
    from pymongo.results import InsertOneResult


@define
class PicrewCountByPostStatus:
    posted: int
    not_posted: int

    @classmethod
    def from_mongo_documents(
        cls, documents: list[dict[str, int | bool]]
    ) -> PicrewCountByPostStatus:
        t = {
            "posted": 0,
            "not_posted": 0,
        }

        for i in documents:
            count = i["count"]

            if i["posted"]:
                t["posted"] = count
            else:
                t["not_posted"] = count

        return cls(**t)


class UserTypeWithId(Protocol):
    id: int

    @property
    def mention(self) -> str:
        pass


@define
class PicrewModel(Model):
    user: UserTypeWithId | None
    link: str
    add_date: datetime
    was_posted: bool
    id: ObjectId = field(default=None)
    tw: str | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)

        if self.user:
            out["user"] = self.user

        id = out.pop("id", None)

        if id:
            out["_id"] = id

        return out

    def to_raw(self) -> dict[str, Any]:
        out = self.to_dict()
        if (user := out["user"]) is not None:
            out["user"] = user.id

        return out

    async def set_to_posted(self, db: AsyncIOMotorDatabase) -> None:
        if self.was_posted:
            return

        self.was_posted = True
        await self.save(db)

    @classmethod
    def from_raw(cls, post: Mapping[str, Any]) -> PicrewModel:
        post = {**post}
        _id = post.pop("_id", None)

        return cls(id=_id, **post)

    async def save(self, db: AsyncIOMotorDatabase) -> None:
        col = db.picrew
        document = self.to_raw()

        if self.id:
            await cast(Awaitable, col.update_one({"_id": self.id}, {"$set": document}))
        else:
            try:
                result: InsertOneResult = await cast(
                    Awaitable, col.insert_one(document)
                )
            except WriteError as e:
                if e.code == 11000:
                    raise DuplicateError("Duplicate picrew link")
                raise e
            else:
                self.id = result.inserted_id

    @classmethod
    async def get(
        cls, db: AsyncIOMotorDatabase, pipeline: list[dict[str, Any]]
    ) -> list[PicrewModel]:
        col = db.picrew
        aggregator = col.aggregate(pipeline)
        bot = Robomania.get_bot()

        out = []

        async for i in aggregator:
            data = {**i}
            user_id = data["user"]
            if user_id is not None and (user := bot.get_user(user_id)) is None:
                try:
                    user = await bot.fetch_user(data["user"])
                except disnake.NotFound:
                    user = None
            else:
                user = None

            data["user"] = user

            model = cls.from_raw(data)

            out.append(model)

        return out

    @classmethod
    async def get_random_unposted(
        cls, db: AsyncIOMotorDatabase, count: int
    ) -> list[PicrewModel]:
        pipeline: list[dict] = [
            {"$match": {"was_posted": False}},
            {"$sample": {"size": count}},
        ]

        return await cls.get(db, pipeline)

    @classmethod
    async def get_random(
        cls, db: AsyncIOMotorDatabase, count: int
    ) -> list[PicrewModel]:
        pipeline: list[dict] = [{"$sample": {"size": count}}]

        return await cls.get(db, pipeline)

    @classmethod
    async def count_posted_and_not_posted(
        cls, db: AsyncIOMotorDatabase
    ) -> PicrewCountByPostStatus:
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$was_posted", "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "posted": "$_id", "count": 1}},
        ]

        results: list[dict[str, int | bool]] = await cast(
            Coroutine, db.picrew.aggregate(pipeline)
        ).to_list(  # type: ignore
            None
        )

        return PicrewCountByPostStatus.from_mongo_documents(results)

    @staticmethod
    def create_collections(db: Database) -> None:
        import pymongo

        col = db.picrew
        col.create_index([("link", pymongo.DESCENDING)], unique=True)
