from dataclasses import dataclass
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