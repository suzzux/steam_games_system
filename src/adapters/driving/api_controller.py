from src.ports.inbound import IngestGameCommandPort
from src.services.query_service import GameQueryService
from src.ports.dtos import GameCreateCommandDTO

class GameAPIController:
    """Контролер приймає HTTP запити і делегує їх відповідним портам"""
    def __init__(self, command_port: IngestGameCommandPort, query_port: GameQueryService):
        self.command_port = command_port
        self.query_port = query_port

    def post_game(self, json_data: dict):
        cmd = GameCreateCommandDTO(**json_data)
        return self.command_port.ingest_game(cmd)

    def search(self, q: str):
        return self.query_port.search_games(q)

    def filter(self, platform: str, designer: str):
        return self.query_port.filter_by_relations(platform, designer)