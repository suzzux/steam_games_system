"""Map-reduce на двох «шардах» (окремі mongomock-клієнти) порівнюється з агрегацією по всій колекції."""
import mongomock

from src.adapters.driven.mongo_mapper import game_to_document
from src.adapters.driven.mongo_shard_adapter import MongoShardAnalyticsAdapter, shard_uri_from_host
from src.services.analytics_service import ShardAnalyticsService
from src.services.mappers import command_to_game
from src.ports.dtos import MapReduceQueryDTO
from tests.sample_data import commands


def make_cluster():
    router = mongomock.MongoClient()               # «mongos»: бачить усі документи
    shard1, shard2 = mongomock.MongoClient(), mongomock.MongoClient()
    for i, cmd in enumerate(commands()):
        doc = game_to_document(command_to_game(cmd, cmd.game_id))
        router["steam"]["games"].insert_one(dict(doc))
        (shard1 if i % 2 == 0 else shard2)["steam"]["games"].insert_one(dict(doc))
    return MongoShardAnalyticsAdapter(router, "steam", shard_clients={"rs-shard1": shard1, "rs-shard2": shard2})


def test_map_reduce_matches_router_aggregation():
    service = ShardAnalyticsService(make_cluster())
    result = service.run_map_reduce(MapReduceQueryDTO(group_by="genres", top_n=50))
    assert result.verified is True
    rows = {r.key: r for r in result.rows}
    assert rows["Action"].games == 4 and rows["Indie"].games == 4
    assert rows["Casual"].avg_price == round((4.99 + 0.0) / 2, 2)
    assert sum(s.matched_docs for s in result.shards) == 5
    assert [s.shard for s in result.shards] == ["rs-shard1", "rs-shard2"]


def test_map_reduce_with_filters():
    service = ShardAnalyticsService(make_cluster())
    result = service.run_map_reduce(MapReduceQueryDTO(group_by="engine", platform="PS5", year_from=2016))
    assert {(r.key, r.games) for r in result.rows} == {("Unity", 1), ("Godot", 1)}


def test_shard_uri():
    assert shard_uri_from_host("rs-shard1/shard1a:27017,shard1b:27017") == \
        "mongodb://shard1a:27017,shard1b:27017/?replicaSet=rs-shard1&readPreference=secondaryPreferred"
