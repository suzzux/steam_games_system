from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class GameCreateCommandDTO:
    name: str
    price: float
    min_age: int
    release_date: str
    short_description: str
    detailed_description: str
    engine: str
    genres: List[str] = field(default_factory=list)
    developers: List[str] = field(default_factory=list)
    publishers: List[str] = field(default_factory=list)
    designers: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    game_id: Optional[int] = None
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

@dataclass
class GameResponseDTO:
    game_id: int
    name: str
    price: float
    name_with_price: Optional[str] = None