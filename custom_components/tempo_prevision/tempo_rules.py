"""Tempo rules for adjusting forecast colors.

Sundays / French holidays / Saturdays: red never occurs on weekends or holidays.
"""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .forecast import ForecastDay

_LOGGER = logging.getLogger(__name__)

# Fixed French holidays (month, day)
FIXED_HOLIDAYS: List[Tuple[int, int]] = [
    (1, 1),  # Jour de l'An
    (5, 1),  # Fête du Travail
    (5, 8),  # Victoire 1945
    (7, 14),  # Fête Nationale
    (8, 15),  # Assomption
    (11, 1),  # Toussaint
    (11, 11),  # Armistice
    (12, 25),  # Noël
]


def compute_easter(year: int) -> datetime.date:
    """Compute Easter Sunday (Butcher-Meeus), valid for years 1583-4099."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)


def get_movable_holidays(year: int) -> List[datetime.date]:
    """Movable French holidays derived from Easter."""
    easter = compute_easter(year)
    return [
        easter + datetime.timedelta(days=1),  # Lundi de Pâques
        easter + datetime.timedelta(days=39),  # Ascension
        easter + datetime.timedelta(days=50),  # Lundi de Pentecôte
    ]


def is_french_holiday(date: datetime.date) -> bool:
    """Return True if date is a French public holiday."""
    if (date.month, date.day) in FIXED_HOLIDAYS:
        return True

    try:
        return date in get_movable_holidays(date.year)
    except Exception as exc:
        _LOGGER.error("Error computing movable holidays for %s: %s", date.year, exc)
        return False


def adjust_forecast_day(forecast: "ForecastDay") -> "ForecastDay":
    """Adjust a single forecast day according to Tempo rules.

    Priority:
    1. Sundays → blue + indicator "D"
    2. Holidays with red → white + "F"
    3. Holidays with allowed colors → keep + "F"
    4. Saturdays with red → white (adjusted probability)
    5. Otherwise → keep original
    """
    from .forecast import ForecastDay

    date = forecast.date
    weekday = date.weekday()  # 0=Monday, 5=Saturday, 6=Sunday

    if weekday == 6:  # Sunday
        return ForecastDay(
            date=date,
            color="bleu",
            probability=None,
            indicator="D",
            source=forecast.source,
        )

    if is_french_holiday(date):
        if forecast.color == "rouge":
            original_prob = (
                forecast.probability if forecast.probability is not None else 0.0
            )
            if original_prob > 0.6:
                new_probability = 1.0
            else:
                new_probability = min(original_prob + 0.1, 1.0)
            return ForecastDay(
                date=date,
                color="blanc",
                probability=new_probability,
                indicator="F",
                source=forecast.source,
            )
        return ForecastDay(
            date=date,
            color=forecast.color,
            probability=forecast.probability,
            indicator="F",
            source=forecast.source,
        )

    if weekday == 5 and forecast.color == "rouge":  # Saturday
        original_prob = (
            forecast.probability if forecast.probability is not None else 0.0
        )
        if original_prob > 0.6:
            new_probability = 1.0
        else:
            new_probability = min(original_prob + 0.1, 1.0)

        return ForecastDay(
            date=date,
            color="blanc",
            probability=new_probability,
            indicator=None,
            source=forecast.source,
        )

    return ForecastDay(
        date=forecast.date,
        color=forecast.color,
        probability=forecast.probability,
        indicator=None,
        source=forecast.source,
    )


def apply_tempo_rules(forecasts: List["ForecastDay"]) -> List["ForecastDay"]:
    """Apply Tempo rules to a list of forecasts."""
    return [adjust_forecast_day(forecast) for forecast in forecasts]
