from src.ports.inbound import IngestGameCommandPort
from src.ports.outbound import GameDocumentRepositoryPort, EventPublisherPort
from src.ports.dtos import GameCreateCommandDTO
from src.domain.value_objects import Price, AgeRestriction
from src.domain.entities import Game

class GameCommandService(IngestGameCommandPort):
    """Обробка потоку команд (Запис)"""
    def __init__(self, document_repo: GameDocumentRepositoryPort, event_publisher: EventPublisherPort):
        self.document_repo = document_repo
        self.event_publisher = event_publisher

    def ingest_game(self, command: GameCreateCommandDTO) -> int:
        # Валідація та створення об'єктів-значень
        price = Price(amount=command.price)
        age_restriction = AgeRestriction(minimum_age=command.min_age)
        
        new_game = Game(
            game_id=0, # Генерується БД
            name=command.name,
            price=price,
            age_restriction=age_restriction,
            # ... інші поля мапляться тут
        )
        saved_game = self.document_repo.save(new_game)
        self.event_publisher.publish_game_created_event(saved_game.game_id)
        return saved_game.game_id