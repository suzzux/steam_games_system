from typing import Optional
from src.ports.outbound import GameDocumentRepositoryPort
from src.domain.entities import Game

class MongoAdapter(GameDocumentRepositoryPort):
    def save(self, game: Game) -> Game: pass
    def find_by_id(self, game_id: int) -> Optional[Game]: pass