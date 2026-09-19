from dataclasses import dataclass

# --- Об'єкти-значення (Value Objects) ---
@dataclass(frozen=True)
class Price:
    amount: float
    currency: str = "USD"

@dataclass(frozen=True)
class ReleaseDate:
    date_str: str

@dataclass(frozen=True)
class AgeRestriction:
    minimum_age: int
    
    def is_restricted(self, user_age: int) -> bool:
        return user_age < self.minimum_age