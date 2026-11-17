from typing import List, Optional

from src.ports.inbound import (
    IngestGameCommandPort, UpdateGameCommandPort, DeleteGameCommandPort,
    SearchGamesQueryPort, GetGameDetailsQueryPort, FilterGamesByRelationsQueryPort, ListGamesQueryPort,
    ShardAnalyticsQueryPort, MonitoringQueryPort,
)
from src.ports.dtos import (
    GameCreateCommandDTO, GameFilterDTO, PageDTO, FacetsDTO, GameResponseDTO, SearchResultDTO,
    MapReduceQueryDTO, MapReduceResultDTO, ShardDistributionDTO, MonitoringDTO,
)


class GameAPIController:
    """Контролер приймає запити (з веб-сторінок або JSON API), перетворює їх у DTO
    і делегує вхідним портам. Від конкретних сервісів він не залежить."""

    def __init__(self, command_port: IngestGameCommandPort, update_port: UpdateGameCommandPort,
                 delete_port: DeleteGameCommandPort, list_port: ListGamesQueryPort,
                 details_port: GetGameDetailsQueryPort, search_port: SearchGamesQueryPort,
                 filter_port: FilterGamesByRelationsQueryPort,
                 analytics_port: Optional[ShardAnalyticsQueryPort] = None,
                 monitoring_port: Optional[MonitoringQueryPort] = None):
        self.command_port = command_port
        self.update_port = update_port
        self.delete_port = delete_port
        self.list_port = list_port
        self.details_port = details_port
        self.search_port = search_port
        self.filter_port = filter_port
        self.analytics_port = analytics_port
        self.monitoring_port = monitoring_port

    # ---------------------------------------------------------------- команди
    def post_game(self, json_data: dict) -> int:
        cmd = GameCreateCommandDTO(**json_data)
        return self.command_port.ingest_game(cmd)

    def put_game(self, game_id: int, json_data: dict) -> int:
        cmd = GameCreateCommandDTO(**dict(json_data, game_id=game_id))
        return self.update_port.update_game(cmd)

    def delete_game(self, game_id: int) -> bool:
        return self.delete_port.delete_game(game_id)

    # ---------------------------------------------------------------- запити
    def list_games(self, params: dict) -> PageDTO:
        return self.list_port.list_games(GameFilterDTO(**params))

    def facets(self) -> FacetsDTO:
        return self.list_port.get_facets()

    def get_game(self, game_id: int) -> GameResponseDTO:
        return self.details_port.get_details(game_id)

    def search(self, q: str) -> SearchResultDTO:
        return self.search_port.search_games(q)

    def autocomplete(self, prefix: str) -> List[str]:
        return self.search_port.autocomplete(prefix)

    def filter(self, platform: str, designer: str) -> SearchResultDTO:
        return self.filter_port.filter_by_relations(platform, designer)

    def map_reduce(self, params: dict) -> MapReduceResultDTO:
        return self.analytics_port.run_map_reduce(MapReduceQueryDTO(**params))

    def shard_distribution(self) -> List[ShardDistributionDTO]:
        return self.analytics_port.shard_distribution()

    def monitoring(self) -> MonitoringDTO:
        return self.monitoring_port.get_counters()
