import pytest

from src.domain.value_objects import Price, ReleaseDate, AgeRestriction
from src.domain.services import QueryNormalizer


def test_price_cannot_be_negative():
    with pytest.raises(ValueError):
        Price(-1)
    assert Price(9.999).amount == 10.0


def test_release_date_parsing():
    assert ReleaseDate.parse("Oct 21, 2008").date_str == "2008-10-21"
    assert ReleaseDate.parse("Oct 2008").date_str == "2008-10-01"
    assert ReleaseDate.parse("").is_released is False
    assert ReleaseDate.parse("Coming soon").date_str == ""
    with pytest.raises(ValueError):
        ReleaseDate.parse("21/10/2008 ???")


def test_age_restriction_range():
    with pytest.raises(ValueError):
        AgeRestriction(30)
    assert AgeRestriction(18).is_restricted(16)


def test_query_normalizer_sorts_tokens():
    assert QueryNormalizer.normalize("  Space   SHOOTER ") == QueryNormalizer.normalize("shooter, space")
