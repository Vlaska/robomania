from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, Type, TypeVar

if TYPE_CHECKING:
    from pymongo.database import Database


TModel = TypeVar('TModel', bound='Model')


class Model(Protocol):
    @abstractmethod
    async def save(self, db: Database) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_raw(cls: Type[TModel], data: dict[str, Any]) -> TModel:
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError
