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