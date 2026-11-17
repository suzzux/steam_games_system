"""Доменні сервіси: логіка, яка не належить одній сутності."""
import math
import re

from .entities import Game

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


class QueryNormalizer:
    """Нормалізує пошуковий запит перед зверненням до кешу та пошукового порту.

    Нижній регістр, видалення зайвих символів і пробілів, сортування токенів
    за алфавітом. Завдяки цьому запити «Space Shooter» і «shooter  space»
    мають однаковий ключ у Redis.
    """

    @staticmethod
    def tokens(query: str):
        return sorted(set(_TOKEN_RE.findall((query or "").lower())))

    @classmethod
    def normalize(cls, query: str) -> str:
        return " ".join(cls.tokens(query))


class EngagementCalculator:
    """Похідна метрика залученості гравців.

    engagement_score = log10(1 + peak_ccu) * log10(1 + average_playtime_forever)
    Логарифм потрібен, бо значення в датасеті відрізняються на кілька порядків.
    """

    @staticmethod
    def score(game: Game) -> float:
        return round(math.log10(1 + game.peak_ccu) * math.log10(1 + game.average_playtime_forever), 2)
