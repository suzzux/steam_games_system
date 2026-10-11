from src.ports.inbound import IngestGameCommandPort
from src.ports.outbound import GameDocumentRepositoryPort, EventPublisherPort
from src.ports.dtos import GameCreateCommandDTO
from src.domain.value_objects import Price, AgeRestriction, ReleaseDate
from src.domain.entities import (
    Game,
    Studio,
    Designer,
    Genre,
    Platform,
    Engine
)

class GameCommandService(IngestGameCommandPort):
    """Обробка потоку команд (Запис)"""

    def __init__(self, document_repo: GameDocumentRepositoryPort, event_publisher: EventPublisherPort):
        self.document_repo = document_repo
        self.event_publisher = event_publisher

    def ingest_game(self, command: GameCreateCommandDTO) -> int:
        # Створення та валідація об'єктів-значень (Value Objects)
        price = Price(amount=command.price)
        age_restriction = AgeRestriction(minimum_age=command.min_age)
        release_date = ReleaseDate(date_str=command.release_date)

        # Мапінг списків рядків у відповідні сутності доменного ядра (Entities)
        genres = [Genre(name=genre_name) for genre_name in command.genres]
        developers = [Studio(name=dev_name) for dev_name in command.developers]
        publishers = [Studio(name=pub_name) for pub_name in command.publishers]
        designers = [Designer(name=designer_name) for designer_name in command.designers]
        platforms = [Platform(name=platform_name) for platform_name in command.platforms]
        engine = Engine(name=command.engine)

        # Складання повного агрегату Game
        new_game = Game(
            game_id=command.game_id if command.game_id else 0,
            name=command.name,
            release_date=release_date,
            price=price,
            age_restriction=age_restriction,
            short_description=command.short_description,
            detailed_description=command.detailed_description,
            genres=genres,
            developers=developers,
            publishers=publishers,
            designers=designers,
            platforms=platforms,
            engine=engine,
            game_trailer=getattr(command, "game_trailer", ""),
            reviews=getattr(command, "reviews", ""),
            dlc_count=getattr(command, "dlc_count", 0),
            achievements=getattr(command, "achievements", 0),
            estimated_owners=getattr(command, "estimated_owners", "0 - 20000"),
            peak_ccu=getattr(command, "peak_ccu", 0),
            positive=getattr(command, "positive", 0),
            negative=getattr(command, "negative", 0),
            recommendations=getattr(command, "recommendations", 0),
            average_playtime_forever=getattr(command, "average_playtime_forever", 0),
            median_playtime_2weeks=getattr(command, "median_playtime_2weeks", 0),
            categories=getattr(command, "categories", []),
            supported_languages=getattr(command, "supported_languages", []),
            full_audio_languages=getattr(command, "full_audio_languages", []),
        )

        # Збереження в MongoDB та публікація події синхронізації (Kafka)
        saved_game = self.document_repo.save(new_game)
        self.event_publisher.publish_game_created_event(saved_game.game_id)
        return saved_game.game_id