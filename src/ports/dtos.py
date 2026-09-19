from dataclasses import dataclass
from typing import List

# --- DTOs (Data Transfer Objects) ---
@dataclass
class GameCreateCommandDTO:
    name: str
    price: float
    min_age: int
    detailed_description: str
    platforms: List[str]
    designers: List[str]

@dataclass
class GameResponseDTO:
    game_id: int
    name: str
    price: float