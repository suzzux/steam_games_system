from typing import List
from abc import ABC, abstractmethod
from .dtos import GameCreateCommandDTO, GameResponseDTO

# --- Вхідні Порти (Inbound Ports / Use Cases - CQRS) ---
class IngestGameCommandPort(ABC):
    @abstractmethod
    def ingest_game(self, command: GameCreateCommandDTO) -> int: pass

class SearchGamesQueryPort(ABC):
    @abstractmethod
    def search_games(self, query: str) -> List[GameResponseDTO]: pass

class GetGameDetailsQueryPort(ABC):
    @abstractmethod
    def get_details(self, game_id: int) -> GameResponseDTO: pass

class FilterGamesByRelationsQueryPort(ABC):
    @abstractmethod
    def filter_by_relations(self, platform_name: str, designer_name: str) -> List[GameResponseDTO]: pass