"""Перетворення DTO <-> доменні сутності (щоб сервіси не дублювали цей код)."""
from src.domain.entities import Game, Studio, Designer, Genre, Platform, Engine
from src.domain.services import EngagementCalculator
from src.domain.value_objects import Price, AgeRestriction, ReleaseDate
from src.ports.dtos import GameCreateCommandDTO, GameResponseDTO, GameListItemDTO


def command_to_game(command: GameCreateCommandDTO, game_id: int) -> Game:
    # Створення та валідація об'єктів-значень (Value Objects)
    price = Price(amount=command.price)
    age_restriction = AgeRestriction(minimum_age=command.min_age)
    release_date = ReleaseDate.parse(command.release_date)

    # Складання повного агрегату Game зі списків рядків
    return Game(
        game_id=game_id,
        name=command.name.strip(),
        release_date=release_date,
        price=price,
        age_restriction=age_restriction,
        short_description=command.short_description,
        detailed_description=command.detailed_description,
        genres=[Genre(n) for n in command.genres],
        developers=[Studio(n) for n in command.developers],
        publishers=[Studio(n) for n in command.publishers],
        designers=[Designer(n) for n in command.designers],
        platforms=[Platform(n) for n in command.platforms],
        engine=Engine(command.engine or ""),
        game_trailer=command.game_trailer,
        reviews=command.reviews,
        dlc_count=command.dlc_count,
        achievements=command.achievements,
        estimated_owners=command.estimated_owners,
        peak_ccu=command.peak_ccu,
        positive=command.positive,
        negative=command.negative,
        recommendations=command.recommendations,
        average_playtime_forever=command.average_playtime_forever,
        median_playtime_2weeks=command.median_playtime_2weeks,
        categories=list(command.categories),
        supported_languages=list(command.supported_languages),
        full_audio_languages=list(command.full_audio_languages),
    )


def _names(items):
    return [i.name for i in items]


def game_to_response(game: Game, shard: str = None) -> GameResponseDTO:
    return GameResponseDTO(
        game_id=game.game_id,
        name=game.name,
        price=game.price.amount,
        name_with_price=f"{game.name} (${game.price.amount:.2f})",
        release_date=game.release_date.date_str,
        required_age=game.age_restriction.minimum_age,
        short_description=game.short_description,
        detailed_description=game.detailed_description,
        reviews=game.reviews,
        genres=_names(game.genres),
        categories=list(game.categories),
        developers=_names(game.developers),
        publishers=_names(game.publishers),
        designers=_names(game.designers),
        platforms=_names(game.platforms),
        engine=game.engine.name,
        game_trailer=game.game_trailer,
        supported_languages=list(game.supported_languages),
        full_audio_languages=list(game.full_audio_languages),
        dlc_count=game.dlc_count,
        achievements=game.achievements,
        estimated_owners=game.estimated_owners,
        peak_ccu=game.peak_ccu,
        positive=game.positive,
        negative=game.negative,
        recommendations=game.recommendations,
        average_playtime_forever=game.average_playtime_forever,
        median_playtime_2weeks=game.median_playtime_2weeks,
        positive_ratio=round(game.positive_ratio, 3),
        engagement_score=EngagementCalculator.score(game),
        shard=shard,
    )


def game_to_list_item(game: Game) -> GameListItemDTO:
    return GameListItemDTO(
        game_id=game.game_id,
        name=game.name,
        release_date=game.release_date.date_str,
        price=game.price.amount,
        genres=_names(game.genres),
        developers=_names(game.developers),
        platforms=_names(game.platforms),
        positive_ratio=round(game.positive_ratio, 3),
    )
