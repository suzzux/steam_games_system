from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from src.domain.entities import Game
from .dtos import GameFilterDTO, MapReduceQueryDTO, MapReduceResultDTO, ShardDistributionDTO


# --- Вихідні Порти (Outbound Ports / Інтерфейси БД) ---
class GameDocumentRepositoryPort(ABC):
    """MongoDB: CRUD основної інформації про гру"""

    @abstractmethod
    def save(self, game: Game) -> Game: ...                                 # Create

    @abstractmethod
    def save_many(self, games: List[Game]) -> int: ...                      # Create (пакетно)

    @abstractmethod
    def find_by_id(self, game_id: int) -> Optional[Game]: ...               # Read

    @abstractmethod
    def find_by_ids(self, game_ids: List[int], from_primary: bool = False) -> List[Game]: ...  # Read (пакетно)

    @abstractmethod
    def find_all(self, limit: int = 50, offset: int = 0) -> List[Game]: ...

    @abstractmethod
    def find_page(self, game_filter: GameFilterDTO) -> Tuple[List[Game], int]: ...  # Read (фільтр + пагінація)

    @abstractmethod
    def distinct_values(self, field_name: str) -> List[str]: ...

    @abstractmethod
    def next_game_id(self) -> int: ...

    @abstractmethod
    def update(self, game: Game) -> Game: ...                               # Update

    @abstractmethod
    def delete_by_id(self, game_id: int) -> bool: ...                       # Delete


class FullTextSearchPort(ABC):
    """Elasticsearch: Повнотекстовий пошук"""

    @abstractmethod
    def index_games(self, games: List[Game]) -> int: pass

    @abstractmethod
    def delete_games(self, game_ids: List[int]) -> None: pass

    @abstractmethod
    def search_by_text(self, text_query: str, limit: int = 50) -> List[int]: pass

    @abstractmethod
    def autocomplete(self, prefix: str, limit: int = 8) -> List[str]: pass


class GraphQueryPort(ABC):
    """Neo4j: Зв'язки сутностей у вигляді графа (вузли та ребра)"""

    @abstractmethod
    def upsert_games(self, games: List[Game]) -> int: pass

    @abstractmethod
    def delete_games(self, game_ids: List[int]) -> None: pass

    @abstractmethod
    def find_games_by_platform_and_designer(self, platform: str, designer: str, limit: int = 100) -> List[int]: pass


class CachePort(ABC):
    """Redis: In-Memory кеш та лічильники"""

    @abstractmethod
    def get_search_cache(self, normalized_query: str) -> Optional[List[int]]: pass

    @abstractmethod
    def set_search_cache(self, normalized_query: str, game_ids: List[int], ttl: int) -> None: pass

    @abstractmethod
    def get_filter_cache(self, platform: str, designer: str) -> Optional[List[int]]: pass

    @abstractmethod
    def set_filter_cache(self, platform: str, designer: str, game_ids: List[int], ttl: int) -> None: pass

    @abstractmethod
    def get_json(self, key: str): pass

    @abstractmethod
    def set_json(self, key: str, value, ttl: int) -> None: pass

    @abstractmethod
    def increment(self, counter: str, amount: int = 1) -> int: pass

    @abstractmethod
    def get_counters(self) -> Dict[str, int]: pass


class EventPublisherPort(ABC):
    """Опублікування подій для синхронізації сховищ"""

    @abstractmethod
    def publish_game_created_event(self, game_id: int) -> None: pass

    @abstractmethod
    def publish_game_deleted_event(self, game_id: int) -> None: pass

    @abstractmethod
    def flush(self) -> None: pass


class ShardedAnalyticsPort(ABC):
    """MongoDB (шардований кластер): map-reduce по шардах і статистика розподілу"""

    @abstractmethod
    def map_reduce(self, query: MapReduceQueryDTO) -> MapReduceResultDTO: pass

    @abstractmethod
    def aggregate_via_router(self, query: MapReduceQueryDTO) -> MapReduceResultDTO: pass

    @abstractmethod
    def shard_distribution(self) -> List[ShardDistributionDTO]: pass

    @abstractmethod
    def locate_shard(self, game_id: int) -> Optional[str]: pass
