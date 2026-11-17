from typing import List
from abc import ABC, abstractmethod
from .dtos import (
    GameCreateCommandDTO, GameResponseDTO, GameFilterDTO, PageDTO, FacetsDTO,
    SearchResultDTO, IngestReportDTO, MapReduceQueryDTO, MapReduceResultDTO,
    ShardDistributionDTO, MonitoringDTO,
)


# --- Вхідні Порти (Inbound Ports / Use Cases - CQRS) ---

# ---------- команди
class IngestGameCommandPort(ABC):
    @abstractmethod
    def ingest_game(self, command: GameCreateCommandDTO) -> int: pass

    @abstractmethod
    def ingest_many(self, commands: List[GameCreateCommandDTO]) -> IngestReportDTO: pass


class UpdateGameCommandPort(ABC):
    @abstractmethod
    def update_game(self, command: GameCreateCommandDTO) -> int: pass


class DeleteGameCommandPort(ABC):
    @abstractmethod
    def delete_game(self, game_id: int) -> bool: pass


# ---------- запити
class SearchGamesQueryPort(ABC):
    @abstractmethod
    def search_games(self, query: str) -> SearchResultDTO: pass

    @abstractmethod
    def autocomplete(self, prefix: str) -> List[str]: pass


class GetGameDetailsQueryPort(ABC):
    @abstractmethod
    def get_details(self, game_id: int) -> GameResponseDTO: pass


class FilterGamesByRelationsQueryPort(ABC):
    @abstractmethod
    def filter_by_relations(self, platform_name: str, designer_name: str) -> SearchResultDTO: pass


class ListGamesQueryPort(ABC):
    @abstractmethod
    def list_games(self, game_filter: GameFilterDTO) -> PageDTO: pass

    @abstractmethod
    def get_facets(self) -> FacetsDTO: pass


class ShardAnalyticsQueryPort(ABC):
    @abstractmethod
    def run_map_reduce(self, query: MapReduceQueryDTO) -> MapReduceResultDTO: pass

    @abstractmethod
    def shard_distribution(self) -> List[ShardDistributionDTO]: pass


class MonitoringQueryPort(ABC):
    @abstractmethod
    def get_counters(self) -> MonitoringDTO: pass


# ---------- синхронізація проєкцій (викликається споживачем подій Kafka)
class SyncGameProjectionPort(ABC):
    @abstractmethod
    def sync_games(self, game_ids: List[int]) -> int: pass

    @abstractmethod
    def remove_games(self, game_ids: List[int]) -> int: pass
