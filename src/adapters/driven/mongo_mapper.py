"""Перетворення доменної сутності Game <-> документ MongoDB (поля як у таблиці 1.2 звіту)."""
from src.domain.entities import Game, Studio, Designer, Genre, Platform, Engine
from src.domain.value_objects import Price, AgeRestriction, ReleaseDate


def game_to_document(game: Game) -> dict:
    return {
        "_id": int(game.game_id),                         # game_id = _id = ключ шардування
        "name": game.name,
        "release_date": game.release_date.as_datetime,    # BSON Date або null («ще не вийшла»)
        "price": game.price.amount,
        "required_age": game.age_restriction.minimum_age,
        "dlc_count": game.dlc_count,
        "short_description": game.short_description,
        "detailed_description": game.detailed_description,
        "reviews": game.reviews,
        "estimated_owners": game.estimated_owners,
        "peak_ccu": game.peak_ccu,
        "positive": game.positive,
        "negative": game.negative,
        "recommendations": game.recommendations,
        "achievements": game.achievements,
        "average_playtime_forever": game.average_playtime_forever,
        "median_playtime_2weeks": game.median_playtime_2weeks,
        "supported_languages": list(game.supported_languages),
        "full_audio_languages": list(game.full_audio_languages),
        "genres": [g.name for g in game.genres],
        "categories": list(game.categories),
        "developers": [s.name for s in game.developers],
        "publishers": [s.name for s in game.publishers],
        "game_designers": [d.name for d in game.designers],
        "platforms": [p.name for p in game.platforms],
        "engine": game.engine.name,
        "game_trailer": game.game_trailer,
    }


def document_to_game(doc: dict) -> Game:
    """Документ може бути неповним (проєкція для списків), тому всюди є значення за замовчуванням."""
    return Game(
        game_id=int(doc["_id"]),
        name=doc.get("name") or "(без назви)",
        release_date=ReleaseDate.parse(doc.get("release_date")),
        price=Price(doc.get("price") or 0),
        age_restriction=AgeRestriction(doc.get("required_age") or 0),
        short_description=doc.get("short_description", ""),
        detailed_description=doc.get("detailed_description", ""),
        genres=[Genre(n) for n in doc.get("genres", [])],
        developers=[Studio(n) for n in doc.get("developers", [])],
        publishers=[Studio(n) for n in doc.get("publishers", [])],
        designers=[Designer(n) for n in doc.get("game_designers", [])],
        platforms=[Platform(n) for n in doc.get("platforms", [])],
        engine=Engine(doc.get("engine", "")),
        game_trailer=doc.get("game_trailer", ""),
        reviews=doc.get("reviews", ""),
        dlc_count=doc.get("dlc_count", 0),
        achievements=doc.get("achievements", 0),
        estimated_owners=doc.get("estimated_owners", ""),
        peak_ccu=doc.get("peak_ccu", 0),
        positive=doc.get("positive", 0),
        negative=doc.get("negative", 0),
        recommendations=doc.get("recommendations", 0),
        average_playtime_forever=doc.get("average_playtime_forever", 0),
        median_playtime_2weeks=doc.get("median_playtime_2weeks", 0),
        categories=doc.get("categories", []),
        supported_languages=doc.get("supported_languages", []),
        full_audio_languages=doc.get("full_audio_languages", []),
    )
