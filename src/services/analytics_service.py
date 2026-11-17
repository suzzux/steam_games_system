from typing import List

from src.ports.inbound import ShardAnalyticsQueryPort, MonitoringQueryPort
from src.ports.outbound import ShardedAnalyticsPort, CachePort
from src.ports.dtos import MapReduceQueryDTO, MapReduceResultDTO, ShardDistributionDTO, MonitoringDTO

ALLOWED_GROUP_FIELDS = ("genres", "platforms", "engine", "developers", "publishers", "game_designers")


class ShardAnalyticsService(ShardAnalyticsQueryPort):
    """Збір даних з різних шардів MongoDB (map-reduce) і статистика розподілу документів."""

    def __init__(self, analytics: ShardedAnalyticsPort):
        self.analytics = analytics

    def run_map_reduce(self, query: MapReduceQueryDTO) -> MapReduceResultDTO:
        if query.group_by not in ALLOWED_GROUP_FIELDS:
            raise ValueError(f"Групування за полем {query.group_by} не підтримується")
        query.top_n = min(100, max(1, int(query.top_n)))
        result = self.analytics.map_reduce(query)
        if query.verify:
            # Контроль: той самий запит через mongos, де MongoDB сама розбиває $group між шардами.
            reference = self.analytics.aggregate_via_router(query)
            ours = [(r.key, r.games) for r in result.rows]
            theirs = [(r.key, r.games) for r in reference.rows]
            result.verified = ours == theirs
        return result

    def shard_distribution(self) -> List[ShardDistributionDTO]:
        rows = self.analytics.shard_distribution()
        total = sum(r.documents for r in rows) or 1
        for r in rows:
            r.share = round(r.documents / total, 4)
        return rows


class MonitoringService(MonitoringQueryPort):
    def __init__(self, cache: CachePort):
        self.cache = cache

    def get_counters(self) -> MonitoringDTO:
        return MonitoringDTO(counters=self.cache.get_counters())
