import mongomock
import pytest

from src.adapters.driven.mongo_adapter import MongoAdapter
from src.services.command_service import GameCommandService
from src.services.query_service import GameQueryService
from src.services.sync_service import GameSyncService
from tests.fakes import FakeSearch, FakeGraph, FakeCache, FakePublisher
from tests.sample_data import commands


@pytest.fixture
def system():
    """Повний набір сервісів: MongoDB (mongomock) + фейкові Elasticsearch/Neo4j/Redis/Kafka."""
    client = mongomock.MongoClient()
    repo = MongoAdapter(client, "steam")
    search, graph, cache, publisher = FakeSearch(), FakeGraph(), FakeCache(), FakePublisher()
    cmd = GameCommandService(repo, publisher, cache)
    qry = GameQueryService(cache, search, graph, repo)
    sync = GameSyncService(repo, search, graph, cache)
    report = cmd.ingest_many(commands())
    sync.sync_games([gid for _, gid in publisher.events])     # імітація роботи sync-worker
    return dict(client=client, repo=repo, search=search, graph=graph, cache=cache, publisher=publisher,
                cmd=cmd, qry=qry, sync=sync, report=report)
