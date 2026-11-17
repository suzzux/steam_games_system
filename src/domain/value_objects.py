from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# --- Об'єкти-значення (Value Objects) ---
# Незмінні структури: перевірка інваріантів виконується в __post_init__,
# тому некоректне значення не дійде до жодного сховища.

# Формати дати, які трапляються в датасеті Steam («Oct 21, 2008», «Oct 2008»)
_DATE_FORMATS = ("%b %d, %Y", "%d %b, %Y", "%b %Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class Price:
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount is None or float(self.amount) < 0:
            raise ValueError(f"Ціна не може бути від'ємною: {self.amount}")
        object.__setattr__(self, "amount", round(float(self.amount), 2))

    @property
    def is_free(self) -> bool:
        return self.amount == 0


@dataclass(frozen=True)
class ReleaseDate:
    """Дата релізу у форматі ISO (YYYY-MM-DD) або порожній рядок, якщо гра ще не вийшла."""
    date_str: str = ""

    def __post_init__(self):
        if self.date_str:
            datetime.strptime(self.date_str, "%Y-%m-%d")  # ValueError, якщо формат неправильний

    @classmethod
    def parse(cls, raw) -> "ReleaseDate":
        """Перетворює дату з датасету («Oct 21, 2008») або datetime у ReleaseDate."""
        if raw is None:
            return cls("")
        if isinstance(raw, datetime):
            return cls(raw.strftime("%Y-%m-%d"))
        text = str(raw).strip()
        if not text or text.lower() in ("coming soon", "to be announced", "tba", "nan"):
            return cls("")
        for fmt in _DATE_FORMATS:
            try:
                return cls(datetime.strptime(text, fmt).strftime("%Y-%m-%d"))
            except ValueError:
                continue
        raise ValueError(f"Невідомий формат дати релізу: {raw!r}")

    @property
    def is_released(self) -> bool:
        return bool(self.date_str)

    @property
    def as_datetime(self) -> Optional[datetime]:
        return datetime.strptime(self.date_str, "%Y-%m-%d") if self.date_str else None

    @property
    def year(self) -> Optional[int]:
        return int(self.date_str[:4]) if self.date_str else None


@dataclass(frozen=True)
class AgeRestriction:
    minimum_age: int = 0

    def __post_init__(self):
        if self.minimum_age is None or not 0 <= int(self.minimum_age) <= 21:
            raise ValueError(f"Віковий ценз має бути в межах 0–21: {self.minimum_age}")
        object.__setattr__(self, "minimum_age", int(self.minimum_age))

    def is_restricted(self, user_age: int) -> bool:
        return user_age < self.minimum_age
