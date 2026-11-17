import logging
from typing import List

from src.ports.inbound import IngestGameCommandPort, UpdateGameCommandPort, DeleteGameCommandPort
from src.ports.outbound import GameDocumentRepositoryPort, EventPublisherPort, CachePort
from src.ports.dtos import GameCreateCommandDTO, IngestReportDTO
from src.services.mappers import command_to_game

log = logging.getLogger(__name__)

# Імена атомарних лічильників у Redis (панель моніторингу)
COUNTER_PROCESSED = "stats:generator:processed"
COUNTER_SAVED = "stats:generator:saved"
COUNTER_FAILED = "stats:generator:failed"


class GameCommandService(IngestGameCommandPort, UpdateGameCommandPort, DeleteGameCommandPort):
    """Обробка потоку команд (Запис): MongoDB -> подія в Kafka -> sync-worker"""

    def __init__(self, document_repo: GameDocumentRepositoryPort, event_publisher: EventPublisherPort,
                 cache: CachePort = None):
        self.document_repo = document_repo
        self.event_publisher = event_publisher
        self.cache = cache

    # ------------------------------------------------------------ create
    def ingest_game(self, command: GameCreateCommandDTO) -> int:
        game_id = command.game_id if command.game_id is not None else self.document_repo.next_game_id()
        game = command_to_game(command, game_id)          # валідація через об'єкти-значення
        saved_game = self.document_repo.save(game)        # запис у MongoDB (write concern majority)
        self.event_publisher.publish_game_created_event(saved_game.game_id)
        self.event_publisher.flush()
        return saved_game.game_id

    def ingest_many(self, commands: List[GameCreateCommandDTO]) -> IngestReportDTO:
        """Пакетне завантаження датасету: невалідні рядки пропускаються, решта пишеться одним bulk-запитом."""
        report = IngestReportDTO()
        games = []
        for command in commands:
            report.processed += 1
            try:
                if command.game_id is None:
                    raise ValueError("у рядку датасету немає game_id")
                games.append(command_to_game(command, int(command.game_id)))
            except (ValueError, TypeError) as error:
                report.failed += 1
                if len(report.errors) < 20:
                    report.errors.append(f"{command.game_id}: {error}")
        if games:
            report.saved = self.document_repo.save_many(games)
            for game in games:
                self.event_publisher.publish_game_created_event(game.game_id)
            self.event_publisher.flush()
        if self.cache:
            self.cache.increment(COUNTER_PROCESSED, report.processed)
            self.cache.increment(COUNTER_SAVED, report.saved)
            if report.failed:
                self.cache.increment(COUNTER_FAILED, report.failed)
        return report

    # ------------------------------------------------------------ update
    def update_game(self, command: GameCreateCommandDTO) -> int:
        if command.game_id is None or self.document_repo.find_by_id(command.game_id) is None:
            raise KeyError(f"Гру {command.game_id} не знайдено")
        game = command_to_game(command, int(command.game_id))
        self.document_repo.update(game)
        self.event_publisher.publish_game_created_event(game.game_id)   # подія «гра змінилась»
        self.event_publisher.flush()
        return game.game_id

    # ------------------------------------------------------------ delete
    def delete_game(self, game_id: int) -> bool:
        deleted = self.document_repo.delete_by_id(game_id)
        if deleted:
            self.event_publisher.publish_game_deleted_event(game_id)
            self.event_publisher.flush()
        return deleted
