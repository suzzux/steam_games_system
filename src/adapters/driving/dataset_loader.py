"""Driving-адаптер data-generator: читає оброблений CSV датасету і передає рядки в IngestGameCommandPort."""
import ast
import csv
import logging
import sys
from typing import Iterator, List

from src.ports.inbound import IngestGameCommandPort
from src.ports.dtos import GameCreateCommandDTO, IngestReportDTO

log = logging.getLogger(__name__)
csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))      # описи та відгуки бувають дуже довгими

# Можливі назви колонок у CSV -> поле системи (таблиця 1.2)
COLUMN_ALIASES = {
    "game_id": ["game_id", "appID", "AppID", "app_id"],
    "name": ["name", "Name"],
    "release_date": ["release_date", "Release date"],
    "price": ["price", "Price"],
    "required_age": ["required_age", "Required age"],
    "dlc_count": ["dlc_count", "DLC count"],
    "short_description": ["short_description"],
    "detailed_description": ["detailed_description", "About the game"],
    "reviews": ["reviews", "Reviews"],
    "estimated_owners": ["estimated_owners", "Estimated owners"],
    "peak_ccu": ["peak_ccu", "Peak CCU"],
    "positive": ["positive", "Positive"],
    "negative": ["negative", "Negative"],
    "recommendations": ["recommendations", "Recommendations"],
    "achievements": ["achievements", "Achievements"],
    "average_playtime_forever": ["average_playtime_forever", "Average playtime forever"],
    "median_playtime_2weeks": ["median_playtime_2weeks", "Median playtime two weeks"],
    "supported_languages": ["supported_languages", "Supported languages"],
    "full_audio_languages": ["full_audio_languages", "Full audio languages"],
    "genres": ["genres", "Genres"],
    "categories": ["categories", "Categories"],
    "developers": ["developers", "Developers"],
    "publishers": ["publishers", "Publishers"],
    "game_designers": ["game_designers"],
    "platforms": ["platforms"],
    "engine": ["engine"],
    "game_trailer": ["game_trailer"],
}


def parse_list(raw) -> List[str]:
    """Списки в CSV бувають у вигляді "['Action', 'Indie']" або "Action,Indie"."""
    if raw is None:
        return []
    text = str(raw).strip()
    if not text or text in ("[]", "nan", "None"):
        return []
    if text.startswith("["):
        try:
            return [str(x).strip() for x in ast.literal_eval(text) if str(x).strip()]
        except (ValueError, SyntaxError):
            text = text.strip("[]")
    return [part.strip().strip("'\"") for part in text.split(",") if part.strip().strip("'\"")]


def _int(raw, default=0) -> int:
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _float(raw, default=0.0) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _pick(row: dict, field: str, default=""):
    for column in COLUMN_ALIASES[field]:
        if column in row and row[column] not in (None, ""):
            return row[column]
    return default


def row_to_command(row: dict) -> GameCreateCommandDTO:
    game_id = _pick(row, "game_id", None)
    return GameCreateCommandDTO(
        game_id=_int(game_id, None) if game_id is not None else None,
        name=str(_pick(row, "name")),
        price=_float(_pick(row, "price", 0)),
        min_age=_int(_pick(row, "required_age", 0)),
        release_date=str(_pick(row, "release_date")),
        short_description=str(_pick(row, "short_description")),
        detailed_description=str(_pick(row, "detailed_description")),
        engine=str(_pick(row, "engine")),
        genres=parse_list(_pick(row, "genres")),
        developers=parse_list(_pick(row, "developers")),
        publishers=parse_list(_pick(row, "publishers")),
        designers=parse_list(_pick(row, "game_designers")),
        platforms=parse_list(_pick(row, "platforms")),
        game_trailer=str(_pick(row, "game_trailer")),
        reviews=str(_pick(row, "reviews")),
        dlc_count=_int(_pick(row, "dlc_count", 0)),
        achievements=_int(_pick(row, "achievements", 0)),
        estimated_owners=str(_pick(row, "estimated_owners", "0 - 20000")),
        peak_ccu=_int(_pick(row, "peak_ccu", 0)),
        positive=_int(_pick(row, "positive", 0)),
        negative=_int(_pick(row, "negative", 0)),
        recommendations=_int(_pick(row, "recommendations", 0)),
        average_playtime_forever=_int(_pick(row, "average_playtime_forever", 0)),
        median_playtime_2weeks=_int(_pick(row, "median_playtime_2weeks", 0)),
        categories=parse_list(_pick(row, "categories")),
        supported_languages=parse_list(_pick(row, "supported_languages")),
        full_audio_languages=parse_list(_pick(row, "full_audio_languages")),
    )


def read_batches(path: str, batch_size: int) -> Iterator[List[GameCreateCommandDTO]]:
    with open(path, encoding="utf-8", newline="") as f:
        batch = []
        for row in csv.DictReader(f):
            batch.append(row_to_command(row))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


class DatasetLoader:

    def __init__(self, command_port: IngestGameCommandPort, batch_size: int = 1000):
        self.command_port = command_port
        self.batch_size = batch_size

    def load(self, path: str, limit: int = None) -> IngestReportDTO:
        total = IngestReportDTO()
        for batch in read_batches(path, self.batch_size):
            if limit is not None:
                batch = batch[: max(0, limit - total.processed)]
                if not batch:
                    break
            report = self.command_port.ingest_many(batch)
            total.processed += report.processed
            total.saved += report.saved
            total.failed += report.failed
            total.errors.extend(report.errors[: max(0, 20 - len(total.errors))])
            log.info("Оброблено %d, збережено %d, з помилками %d", total.processed, total.saved, total.failed)
        return total
