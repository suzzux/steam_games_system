from dataclasses import dataclass, field
from typing import List
from .value_objects import ReleaseDate, Price, AgeRestriction


# --- Сутності (Entities) ---
@dataclass
class Studio:
    name: str


@dataclass
class Designer:
    name: str


@dataclass
class Genre:
    name: str


@dataclass
class Platform:
    name: str


@dataclass
class Engine:
    name: str


@dataclass
class Game:
    game_id: int
    name: str
    release_date: ReleaseDate
    price: Price
    age_restriction: AgeRestriction
    short_description: str
    detailed_description: str
    genres: List[Genre]
    developers: List[Studio]
    publishers: List[Studio]
    designers: List[Designer]
    platforms: List[Platform]
    engine: Engine
    game_trailer: str = ""
    reviews: str = ""
    dlc_count: int = 0
    achievements: int = 0
    estimated_owners: str = "0 - 20000"
    peak_ccu: int = 0
    positive: int = 0
    negative: int = 0
    recommendations: int = 0
    average_playtime_forever: int = 0
    median_playtime_2weeks: int = 0
    categories: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=list)
    full_audio_languages: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.game_id is None or int(self.game_id) < 0:
            raise ValueError("game_id має бути невід'ємним цілим числом")
        if not self.name or not str(self.name).strip():
            raise ValueError("Назва гри не може бути порожньою")
        for counter in ("dlc_count", "achievements", "peak_ccu", "positive", "negative",
                        "recommendations", "average_playtime_forever", "median_playtime_2weeks"):
            if getattr(self, counter) < 0:
                raise ValueError(f"Поле {counter} не може бути від'ємним")

    @property
    def positive_ratio(self) -> float:
        """Частка позитивних відгуків (0..1)."""
        total = self.positive + self.negative
        return self.positive / total if total else 0.0
