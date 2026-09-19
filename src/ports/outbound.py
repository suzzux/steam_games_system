from typing import List, Optional
from abc import ABC, abstractmethod
from src.domain.entities import Game

# --- Вихідні Порти (Outbound Ports / Інтерфейси БД) ---
class GameDocumentRepositoryPort(ABC):
    """MongoDB: CRUD основної інформації"""
    @abstractmethod
    def save(self, game: Game) -> Game: pass
    @abstractmethod
    def find_by_id(self, game_id: int) -> Optional[Game]: pass

class FullTextSearchPort(ABC):
    """Elasticsearch: Повнотекстовий пошук"""
    @abstractmethod
    def search_by_text(self, text_query: str) -> List[int]: pass

class RelationalQueryPort(ABC):
    """PostgreSQL: Зв'язки сутностей (багато-до-багатьох)"""
    @abstractmethod
    def find_games_by_platform_and_designer(self, platform: str, designer: str) -> List[int]: pass

class CachePort(ABC):
    """Redis: In-Memory кеш та лічильники"""
    @abstractmethod
    def get_search_cache(self, normalized_query: str) -> Optional[List[int]]: pass
    @abstractmethod
    def set_search_cache(self, normalized_query: str, game_ids: List[int], ttl: int) -> None: pass

class EventPublisherPort(ABC):
    """Опублікування подій для синхронізації сховищ"""
    @abstractmethod
    def publish_game_created_event(self, game_id: int) -> None: pass