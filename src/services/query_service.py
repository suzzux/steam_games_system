from typing import List
from src.ports.inbound import SearchGamesQueryPort, GetGameDetailsQueryPort, FilterGamesByRelationsQueryPort
from src.ports.outbound import CachePort, FullTextSearchPort, RelationalQueryPort, GameDocumentRepositoryPort
from src.ports.dtos import GameResponseDTO

class GameQueryService(SearchGamesQueryPort, GetGameDetailsQueryPort, FilterGamesByRelationsQueryPort):
    """Обробка потоку запитів (Читання з кешуванням)"""
    def __init__(self, cache: CachePort, search: FullTextSearchPort, 
                 relational_db: RelationalQueryPort, document_repo: GameDocumentRepositoryPort):
        self.cache = cache
        self.search = search
        self.relational_db = relational_db
        self.document_repo = document_repo

    def search_games(self, query: str) -> List[GameResponseDTO]:
        normalized = query.lower().strip()
        game_ids = self.cache.get_search_cache(normalized)
        if not game_ids:
            game_ids = self.search.search_by_text(normalized)
            self.cache.set_search_cache(normalized, game_ids, ttl=3600)
        return [self.get_details(g_id) for g_id in game_ids]

    def filter_by_relations(self, platform_name: str, designer_name: str) -> List[GameResponseDTO]:
        # Делегуємо запит до PostgreSQL
        game_ids = self.relational_db.find_games_by_platform_and_designer(platform_name, designer_name)
        return [self.get_details(g_id) for g_id in game_ids]

    def get_details(self, game_id: int) -> GameResponseDTO:
        game = self.document_repo.find_by_id(game_id)
        return GameResponseDTO(game.game_id, game.name, game.price.amount)