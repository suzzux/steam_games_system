import time
from typing import List

from src.domain.services import QueryNormalizer
from src.ports.inbound import (
    SearchGamesQueryPort, GetGameDetailsQueryPort, FilterGamesByRelationsQueryPort, ListGamesQueryPort,
)
from src.ports.outbound import CachePort, FullTextSearchPort, GraphQueryPort, GameDocumentRepositoryPort, \
    ShardedAnalyticsPort
from src.ports.dtos import GameResponseDTO, GameFilterDTO, PageDTO, FacetsDTO, SearchResultDTO
from src.services.mappers import game_to_response, game_to_list_item

SEARCH_TTL = 600        # 10 хв: пошуковий індекс оновлюється із затримкою, тому довше тримати немає сенсу
FILTER_TTL = 600
FACETS_TTL = 3600


class GameQueryService(SearchGamesQueryPort, GetGameDetailsQueryPort, FilterGamesByRelationsQueryPort,
                       ListGamesQueryPort):
    """Обробка потоку запитів (Читання з кешуванням)"""

    def __init__(self, cache: CachePort, search: FullTextSearchPort,
                 graph_db: GraphQueryPort, document_repo: GameDocumentRepositoryPort,
                 shard_info: ShardedAnalyticsPort = None):
        self.cache = cache
        self.search = search
        self.graph_db = graph_db
        self.document_repo = document_repo
        self.shard_info = shard_info

    # ---------------------------------------------------------------- каталог (MongoDB)
    def list_games(self, game_filter: GameFilterDTO) -> PageDTO:
        games, total = self.document_repo.find_page(game_filter)
        return PageDTO(items=[game_to_list_item(g) for g in games], total=total,
                       page=game_filter.page, page_size=game_filter.page_size)

    def get_facets(self) -> FacetsDTO:
        cached = self.cache.get_json("facets:catalog")
        if cached:
            return FacetsDTO(**cached)
        facets = FacetsDTO(genres=self.document_repo.distinct_values("genres"),
                           platforms=self.document_repo.distinct_values("platforms"))
        self.cache.set_json("facets:catalog", facets.__dict__, ttl=FACETS_TTL)
        return facets

    def get_details(self, game_id: int) -> GameResponseDTO:
        game = self.document_repo.find_by_id(game_id)
        if game is None:
            raise KeyError(f"Гру {game_id} не знайдено")
        shard = self.shard_info.locate_shard(game_id) if self.shard_info else None
        return game_to_response(game, shard=shard)

    # ---------------------------------------------------------------- пошук (Redis -> Elasticsearch -> MongoDB)
    def search_games(self, query: str) -> SearchResultDTO:
        started = time.perf_counter()
        normalized = QueryNormalizer.normalize(query)
        if not normalized:
            return SearchResultDTO(query=query, items=[], source="-", elapsed_ms=0.0)
        game_ids = self.cache.get_search_cache(normalized)
        source = "redis"
        if game_ids is None:                                  # Cache Miss
            source = "elasticsearch"
            self.cache.increment("stats:cache:misses")
            game_ids = self.search.search_by_text(normalized)
            self.cache.set_search_cache(normalized, game_ids, ttl=SEARCH_TTL)
        else:
            self.cache.increment("stats:cache:hits")
        items = self._cards_in_order(game_ids)
        return SearchResultDTO(query=query, items=items, source=source,
                               elapsed_ms=round((time.perf_counter() - started) * 1000, 1))

    def autocomplete(self, prefix: str) -> List[str]:
        prefix = (prefix or "").strip()
        return self.search.autocomplete(prefix) if len(prefix) >= 2 else []

    # ---------------------------------------------------------------- фільтр за зв'язками (Redis -> Neo4j -> MongoDB)
    def filter_by_relations(self, platform_name: str, designer_name: str) -> SearchResultDTO:
        started = time.perf_counter()
        game_ids = self.cache.get_filter_cache(platform_name, designer_name)
        source = "redis"
        if game_ids is None:
            source = "neo4j"
            self.cache.increment("stats:cache:misses")
            game_ids = self.graph_db.find_games_by_platform_and_designer(platform_name, designer_name)
            self.cache.set_filter_cache(platform_name, designer_name, game_ids, ttl=FILTER_TTL)
        else:
            self.cache.increment("stats:cache:hits")
        items = self._cards_in_order(game_ids)
        return SearchResultDTO(query=f"{designer_name} @ {platform_name}", items=items, source=source,
                               elapsed_ms=round((time.perf_counter() - started) * 1000, 1))

    def _cards_in_order(self, game_ids: List[int]):
        """Картки читаються з MongoDB одним запитом ($in), порядок як у результаті пошуку."""
        games = {g.game_id: g for g in self.document_repo.find_by_ids(game_ids)}
        return [game_to_list_item(games[i]) for i in game_ids if i in games]
