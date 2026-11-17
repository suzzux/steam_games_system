"""Map-reduce по шардах MongoDB і статистика розподілу документів.

Map:     на кожному шарді (окремому replica set) паралельно виконується агрегація,
         яка рахує ЧАСТКОВІ суми по групах тільки для своїх документів.
Shuffle: часткові результати групуються за ключем (жанр, платформа, ...).
Reduce:  часткові суми складаються, з них рахуються середні значення та частки.

Для контролю той самий запит виконується через mongos (aggregate_via_router),
де MongoDB сама ділить $group на частини для шардів і частину злиття.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable, Dict, List, Optional

from pymongo import MongoClient
from pymongo.read_preferences import ReadPreference

from src.ports.outbound import ShardedAnalyticsPort
from src.ports.dtos import (
    MapReduceQueryDTO, MapReduceResultDTO, GroupStatDTO, ShardPartialDTO, ShardDistributionDTO,
)

ARRAY_FIELDS = {"genres", "platforms", "developers", "publishers", "game_designers"}


def shard_uri_from_host(host: str) -> str:
    """'rs-shard1/shard1a:27017,shard1b:27017' -> URI для прямого підключення до replica set шарду."""
    rs_name, members = host.split("/", 1)
    return f"mongodb://{members}/?replicaSet={rs_name}&readPreference=secondaryPreferred"


def build_match(query: MapReduceQueryDTO) -> dict:
    match = {}
    if query.year_from or query.year_to:
        rng = {}
        if query.year_from:
            rng["$gte"] = datetime(int(query.year_from), 1, 1)
        if query.year_to:
            rng["$lt"] = datetime(int(query.year_to) + 1, 1, 1)
        match["release_date"] = rng
    if query.platform:
        match["platforms"] = query.platform
    return match


def build_map_pipeline(query: MapReduceQueryDTO) -> list:
    """Map-етап: фільтр + часткове групування. Повертає (ключ, часткові суми)."""
    field = query.group_by
    pipeline = [{"$match": build_match(query)}]
    if field in ARRAY_FIELDS:
        pipeline.append({"$unwind": "$" + field})       # одна гра з 3 жанрами дає 3 пари (жанр, гра)
    pipeline.append({"$match": {field: {"$nin": [None, ""]}}})
    pipeline.append({"$group": {
        "_id": "$" + field,
        "games": {"$sum": 1},
        "sum_price": {"$sum": "$price"},
        "sum_positive": {"$sum": "$positive"},
        "sum_negative": {"$sum": "$negative"},
        "max_peak_ccu": {"$max": "$peak_ccu"},
        "free_games": {"$sum": {"$cond": [{"$eq": ["$price", 0]}, 1, 0]}},
    }})
    return pipeline


def reduce_partials(partials: List[List[dict]]) -> Dict[str, dict]:
    """Reduce-етап: складання часткових сум з усіх шардів за ключем групи."""
    merged: Dict[str, dict] = {}
    for rows in partials:
        for row in rows:
            acc = merged.setdefault(str(row["_id"]), {"games": 0, "sum_price": 0.0, "sum_positive": 0,
                                                      "sum_negative": 0, "max_peak_ccu": 0, "free_games": 0})
            acc["games"] += row["games"]
            acc["sum_price"] += row["sum_price"] or 0
            acc["sum_positive"] += row["sum_positive"] or 0
            acc["sum_negative"] += row["sum_negative"] or 0
            acc["free_games"] += row["free_games"]
            acc["max_peak_ccu"] = max(acc["max_peak_ccu"], row["max_peak_ccu"] or 0)
    return merged


def finalize(merged: Dict[str, dict], top_n: int) -> List[GroupStatDTO]:
    rows = []
    for key, acc in merged.items():
        reviews = acc["sum_positive"] + acc["sum_negative"]
        rows.append(GroupStatDTO(
            key=key,
            games=acc["games"],
            avg_price=round(acc["sum_price"] / acc["games"], 2) if acc["games"] else 0.0,
            positive_ratio=round(acc["sum_positive"] / reviews, 3) if reviews else 0.0,
            max_peak_ccu=int(acc["max_peak_ccu"]),
            free_share=round(acc["free_games"] / acc["games"], 3) if acc["games"] else 0.0,
        ))
    rows.sort(key=lambda r: (-r.games, r.key))
    return rows[:top_n]


class MongoShardAnalyticsAdapter(ShardedAnalyticsPort):

    def __init__(self, router_client, db_name: str = "steam", collection: str = "games",
                 shard_clients: Optional[Dict[str, object]] = None,
                 client_factory: Callable[[str], object] = None):
        """router_client - підключення до mongos.
        shard_clients - готові підключення до шардів {назва: client} (використовується в тестах);
        якщо не задано, список шардів читається з config.shards.
        """
        self.router = router_client
        self.db_name = db_name
        self.collection = collection
        self._shard_clients = shard_clients
        self._client_factory = client_factory or (lambda uri: MongoClient(uri, serverSelectionTimeoutMS=5000))

    # ------------------------------------------------------------ підключення до шардів
    def shard_clients(self) -> Dict[str, object]:
        if self._shard_clients is None:
            shards = self.router["config"]["shards"].find({}, {"_id": 1, "host": 1})
            self._shard_clients = {s["_id"]: self._client_factory(shard_uri_from_host(s["host"])) for s in shards}
        return self._shard_clients

    def _shard_collection(self, client):
        return client[self.db_name][self.collection].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED)

    # ------------------------------------------------------------ map-reduce
    def _map_on_shard(self, shard_name: str, client, query: MapReduceQueryDTO):
        started = time.perf_counter()
        coll = self._shard_collection(client)
        rows = list(coll.aggregate(build_map_pipeline(query), allowDiskUse=True))
        matched = coll.count_documents(build_match(query))
        partial = ShardPartialDTO(shard=shard_name, matched_docs=matched, groups=len(rows),
                                  elapsed_ms=round((time.perf_counter() - started) * 1000, 1))
        return partial, rows

    def map_reduce(self, query: MapReduceQueryDTO) -> MapReduceResultDTO:
        started = time.perf_counter()
        clients = self.shard_clients()
        with ThreadPoolExecutor(max_workers=max(1, len(clients))) as pool:      # map - паралельно на всіх шардах
            futures = [pool.submit(self._map_on_shard, name, client, query) for name, client in clients.items()]
            results = [f.result() for f in futures]
        merged = reduce_partials([rows for _, rows in results])                  # shuffle + reduce
        return MapReduceResultDTO(
            query=query,
            rows=finalize(merged, query.top_n),
            shards=sorted((p for p, _ in results), key=lambda p: p.shard),
            total_groups=len(merged),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 1),
        )

    def aggregate_via_router(self, query: MapReduceQueryDTO) -> MapReduceResultDTO:
        started = time.perf_counter()
        coll = self.router[self.db_name][self.collection]
        rows = list(coll.aggregate(build_map_pipeline(query), allowDiskUse=True))
        merged = reduce_partials([rows])
        return MapReduceResultDTO(query=query, rows=finalize(merged, query.top_n), shards=[],
                                  total_groups=len(merged),
                                  elapsed_ms=round((time.perf_counter() - started) * 1000, 1))

    # ------------------------------------------------------------ розподіл даних між шардами
    def shard_distribution(self) -> List[ShardDistributionDTO]:
        coll = self.router[self.db_name][self.collection]
        stats = list(coll.aggregate([{"$collStats": {"storageStats": {}}}]))
        chunks = self._chunks_per_shard()
        return [ShardDistributionDTO(shard=s.get("shard", "?"),
                                     documents=int(s["storageStats"].get("count", 0)),
                                     size_mb=round(s["storageStats"].get("size", 0) / 1024 / 1024, 1),
                                     chunks=chunks.get(s.get("shard"), 0))
                for s in sorted(stats, key=lambda x: x.get("shard", ""))]

    def _chunks_per_shard(self) -> Dict[str, int]:
        config = self.router["config"]
        ns = f"{self.db_name}.{self.collection}"
        meta = config["collections"].find_one({"_id": ns})
        if not meta:
            return {}
        # з MongoDB 5.0 чанки прив'язані до uuid колекції, а не до її імені
        match = {"uuid": meta["uuid"]} if "uuid" in meta else {"ns": ns}
        pipeline = [{"$match": match}, {"$group": {"_id": "$shard", "n": {"$sum": 1}}}]
        return {r["_id"]: r["n"] for r in config["chunks"].aggregate(pipeline)}

    def locate_shard(self, game_id: int) -> Optional[str]:
        """У якому шарді лежить гра: з плану виконання (explain) цільового запиту через mongos."""
        try:
            plan = self.router[self.db_name][self.collection].find({"_id": int(game_id)}).explain()
        except Exception:
            return None
        return _find_key(plan, "shardName")


def _find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find_key(value, key)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_key(value, key)
            if found:
                return found
    return None
