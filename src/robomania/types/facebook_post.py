from __future__ import annotations

import inspect
import logging
from dataclasses import InitVar, asdict, dataclass, field
from typing import (TYPE_CHECKING, Any, Awaitable, Iterable, Type, TypeAlias,
                    TypeVar, cast)

if TYPE_CHECKING:
    from pymongo.database import Database


# TODO: Replace by `typing.Self` when mypy will roll support for it
TFacebookPost = TypeVar('TFacebookPost', bound='FacebookPost')
logger = logging.getLogger('robomania.announcements')


@dataclass()
class FacebookPost:
    timestamp: int
    post_text: str
    post_id: int
    post_url: str
    images: list[str] | None

    EVENT_NAME_MULTILANG = {'event', 'wydarzenie'}

    is_event: bool = field(init=False, default=False)

    post: InitVar[dict[str, Any]]

    @staticmethod
    def _post_contains_event(post: dict[str, Any]) -> bool:
        return any(
            i['name'] in FacebookPost.EVENT_NAME_MULTILANG
            for i in post['with']
            if 'name' in i
        )

    def __post_init__(self, post: dict[str, Any]) -> None:
        if 'is_event' in post:
            self.is_event = post['is_event']
        else:
            self.is_event = bool(
                'with' in post and
                post['with'] and
                self._post_contains_event(post)
            )

    @classmethod
    def from_dict(
        cls: Type[TFacebookPost],
        post: dict[str, Any]
    ) -> TFacebookPost:
        t = post.copy()
        t.pop('is_event', None)
        return cls(**t, post=post)

    @classmethod
    def from_raw(
        cls: Type[TFacebookPost],
        post: dict[str, Any]
    ) -> TFacebookPost:
        post_fields = inspect.signature(cls).parameters

        return cls(**{
            k: v for k, v in post.items()
            if k in post_fields
        }, post=post)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def remove_event_posts(
        posts: FacebookPosts
    ) -> FacebookPosts:

        def condition(x: FacebookPost) -> bool:
            return not (not x.post_text and x.is_event)

        return list(filter(condition, posts))

    @staticmethod
    async def save(db: Database, posts: Iterable[FacebookPost]) -> None:
        col = db.posts

        savable_posts = [i.to_dict() for i in posts]

        await cast(
            Awaitable,
            col.insert_many(savable_posts, ordered=False)
        )

    @staticmethod
    async def latest_timestamp(db: Database) -> int:
        col = db.posts

        latest_post = await cast(Awaitable, col.aggregate([  # type: ignore
            {'$sort': {'timestamp': -1}},
            {'$limit': 1},
            {'$project': {'_id': 0, 'timestamp': 1}}
        ])).to_list(1)

        if latest_post:
            timestamp = latest_post[0]['timestamp']
        else:
            logger.warning('No posts in database, using 0.')
            timestamp = 0

        return timestamp

    @classmethod
    async def get_only_new_posts(
        cls,
        db: Database,
        posts: FacebookPosts
    ) -> FacebookPosts:
        latest_timestamp = await FacebookPost.latest_timestamp(db)
        logger.debug('Filtering out old posts')

        return sorted(
            filter(lambda x: x.timestamp > latest_timestamp, posts),
            key=lambda x: x.timestamp,
        )

    @staticmethod
    async def create_collections(db: Database) -> None:
        import pymongo

        posts = db.posts
        await cast(
            Awaitable,
            posts.create_index([('timestamp', pymongo.DESCENDING)])
        )


FacebookPosts: TypeAlias = list[FacebookPost]
