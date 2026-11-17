import json
from typing import Dict, List, Optional

from src.ports.outbound import CachePort


class RedisAdapter(CachePort):
    """Redis: кеш результатів пошуку/фільтрів (cache-aside з TTL) і атомарні лічильники.

    Ключі:
      search:query:{normalized_tokens}  -> JSON-масив [game_id, ...]
      filter:{platform}:{designer}      -> JSON-масив [game_id, ...]
      facets:catalog                    -> JSON зі списками жанрів і платформ
      stats:*                           -> лічильники (INCR)
    """

    def __init__(self, client):
        self.r = client       # redis.Redis(host=..., decode_responses=True)

    @staticmethod
    def search_key(normalized_query: str) -> str:
        return f"search:query:{normalized_query}"

    @staticmethod
    def filter_key(platform: str, designer: str) -> str:
        return f"filter:{platform.strip().lower()}:{designer.strip().lower()}"

    def _get_ids(self, key: str) -> Optional[List[int]]:
        raw = self.r.get(key)
        return json.loads(raw) if raw is not None else None

    def get_search_cache(self, normalized_query: str) -> Optional[List[int]]:
        return self._get_ids(self.search_key(normalized_query))

    def set_search_cache(self, normalized_query: str, game_ids: List[int], ttl: int) -> None:
        self.r.set(self.search_key(normalized_query), json.dumps(game_ids), ex=ttl)

    def get_filter_cache(self, platform: str, designer: str) -> Optional[List[int]]:
        return self._get_ids(self.filter_key(platform, designer))

    def set_filter_cache(self, platform: str, designer: str, game_ids: List[int], ttl: int) -> None:
        self.r.set(self.filter_key(platform, designer), json.dumps(game_ids), ex=ttl)

    def get_json(self, key: str):
        raw = self.r.get(key)
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value, ttl: int) -> None:
        self.r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)

    def increment(self, counter: str, amount: int = 1) -> int:
        return int(self.r.incrby(counter, amount))           # атомарна операція, безпечна для кількох процесів

    def get_counters(self) -> Dict[str, int]:
        keys = sorted(self.r.scan_iter(match="stats:*", count=100))
        values = self.r.mget(keys) if keys else []
        return {k: int(v or 0) for k, v in zip(keys, values)}
