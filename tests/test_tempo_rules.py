"""Tests for Tempo rules."""
from __future__ import annotations

import datetime

from custom_components.tempo_prevision.forecast import ForecastDay
from custom_components.tempo_prevision.tempo_rules import (
    adjust_forecast_day,
    apply_tempo_rules,
    compute_easter,
    is_french_holiday,
)


def test_fixed_holidays_2025():
    """Fixed French holidays."""
    for d in [
        datetime.date(2025, 1, 1),
        datetime.date(2025, 5, 1),
        datetime.date(2025, 7, 14),
        datetime.date(2025, 12, 25),
    ]:
        assert is_french_holiday(d)


def test_movable_holidays_2025():
    """Easter-based holidays for 2025."""
    assert compute_easter(2025) == datetime.date(2025, 4, 20)
    assert is_french_holiday(datetime.date(2025, 4, 21))  # Easter Monday
    assert is_french_holiday(datetime.date(2025, 5, 29))  # Ascension


def test_sunday_always_blue():
    """Sundays become blue with indicator D."""
    # 2025-01-12 is a Sunday
    forecast = ForecastDay(
        date=datetime.date(2025, 1, 12), color="rouge", probability=0.9
    )
    adjusted = adjust_forecast_day(forecast)
    assert adjusted.color == "bleu"
    assert adjusted.indicator == "D"
    assert adjusted.probability is None


def test_saturday_red_becomes_white_high_prob():
    """Saturday red with high probability → white 100%."""
    # 2025-01-11 is a Saturday
    forecast = ForecastDay(
        date=datetime.date(2025, 1, 11), color="rouge", probability=0.8
    )
    adjusted = adjust_forecast_day(forecast)
    assert adjusted.color == "blanc"
    assert adjusted.probability == 1.0
    assert adjusted.indicator is None


def test_holiday_red_becomes_white():
    """Holiday red → white with indicator F."""
    forecast = ForecastDay(
        date=datetime.date(2025, 7, 14), color="rouge", probability=0.5
    )
    adjusted = adjust_forecast_day(forecast)
    assert adjusted.color == "blanc"
    assert adjusted.indicator == "F"
    assert adjusted.probability == 0.6


def test_weekday_unchanged():
    """Regular weekday keeps color."""
    # 2025-01-15 is a Wednesday
    forecast = ForecastDay(
        date=datetime.date(2025, 1, 15), color="blanc", probability=0.7
    )
    adjusted = adjust_forecast_day(forecast)
    assert adjusted.color == "blanc"
    assert adjusted.probability == 0.7
    assert adjusted.indicator is None


def test_apply_tempo_rules_list():
    """apply_tempo_rules maps over a list."""
    forecasts = [
        ForecastDay(date=datetime.date(2025, 1, 12), color="rouge", probability=0.9),
        ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.8),
    ]
    result = apply_tempo_rules(forecasts)
    assert result[0].color == "bleu"
    assert result[1].color == "bleu"
