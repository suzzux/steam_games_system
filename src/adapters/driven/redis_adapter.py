from typing import List, Optional
from src.ports.outbound import CachePort

class RedisAdapter(CachePort):
    def get_search_cache(self, normalized_query: str) -> Optional[List[int]]: pass
    def set_search_cache(self, query: str, ids: List[int], ttl: int) -> None: pass