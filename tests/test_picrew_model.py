from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import disnake
import pytest
from bson import ObjectId
from faker import Faker
from mongomock_motor import AsyncMongoMockClient
from pytest_mock import MockerFixture

from robomania.types.picrew_model import PicrewCountByPostStatus, PicrewModel

if TYPE_CHECKING:
    from robomania.bot import Robomania


class TestPicrewCountByPostStatus:
    @pytest.mark.parametrize('documents,result', [
        [[], PicrewCountByPostStatus(0, 0)],
        [[{'posted': True, 'count': 20}], PicrewCountByPostStatus(20, 0)],
        [[{'posted': False, 'count': 20}], PicrewCountByPostStatus(0, 20)],
        [[
            {'posted': True, 'count': 10},
            {'posted': False, 'count': 5}
        ], PicrewCountByPostStatus(10, 5)],
    ])
    def test_from_mongo_documents(self, documents, result) -> None:
        out = PicrewCountByPostStatus.from_mongo_documents(documents)
        assert out == result


class TestPicrewModel:
    date = datetime.now()
    document = {
        'user': None,
        'link': 'https://example.org',
        'add_date': date,
        'was_posted': True,
        '_id': None,
    }

    @pytest.fixture
    def raw_model(self, user) -> dict:
        out = self.document.copy()
        out['user'] = user.id
        return out

    @pytest.fixture
    def model(self, user, raw_model: dict) -> PicrewModel:
        return PicrewModel(
            user,
            raw_model['link'],
            raw_model['add_date'],
            raw_model['was_posted'],
            raw_model['_id'],
        )

    @pytest.fixture
    def user(self, bot: Robomania, mocker: MockerFixture) -> MagicMock:
        usr = mocker.Mock(spec=disnake.User)
        usr.id = 413

        mocker.patch.object(bot, 'get_user').return_value = usr
        mocker.patch('disnake.Client.get_user').return_value = usr

        return usr

    @staticmethod
    def create(faker: Faker, was_posted: bool, user) -> PicrewModel:
        date = faker.date_time()

        return PicrewModel(
            user,
            faker.url(),
            date,
            was_posted,
            ObjectId.from_datetime(date)
        )

    def test_to_dict(self, user, raw_model: dict) -> None:
        model = PicrewModel(
            user=user,
            link='https://example.org',
            add_date=self.date,
            was_posted=True,
        )
        result = raw_model.copy()
        result.pop('_id')

        assert model.to_dict() == result

        id = ObjectId.from_datetime(self.date)
        result['_id'] = id
        model.id = id

        assert model.to_dict() == result

    def test_from_raw(self, raw_model, model: PicrewModel) -> None:
        id = ObjectId.from_datetime(self.date)
        raw_model['_id'] = id
        model.id = id

        assert model == PicrewModel.from_raw(raw_model)

    @pytest.mark.asyncio
    async def test_save_insert(
        self,
        client: AsyncMongoMockClient,
        model: PicrewModel
    ) -> None:
        model.id = None
        await model.save(client.db)

        assert model.id
        assert await client.db.picrew.count_documents({}) == 1

    @pytest.mark.asyncio
    async def test_save_update(
        self,
        client: AsyncMongoMockClient,
        model: PicrewModel,
    ) -> None:
        model.id = None
        await model.save(client.db)

        new_add_date = datetime.now().replace(microsecond=0)
        model.add_date = new_add_date
        await model.save(client.db)

        result = (await client.db.picrew.find({'_id': model.id}).to_list())[0]
        assert result['add_date'] == new_add_date

    @pytest.mark.asyncio
    async def test_get_random_unposted(
        self,
        client: AsyncMongoMockClient,
        faker: Faker,
        user
    ) -> None:
        data = [self.create(faker, True, user).to_dict() for _ in range(6)]
        ids = set()

        for _ in range(3):
            t = self.create(faker, False, user)
            data.append(t.to_dict())
            ids.add(t.id)

        await client.db.picrew.insert_many(data)
        results = await PicrewModel.get_random_unposted(client.db, 9)

        assert len(results) == 3
        assert all(i.id in ids for i in results)

    @pytest.mark.asyncio
    async def test_count_posted_and_not_posted(
        self,
        client: AsyncMongoMockClient
    ) -> None:
        documents = [{'was_posted': True} for _ in range(5)]
        documents.extend({'was_posted': False} for _ in range(3))

        await client.db.picrew.insert_many(documents)
        results = await PicrewModel.count_posted_and_not_posted(client.db)
        assert results == PicrewCountByPostStatus(5, 3)
