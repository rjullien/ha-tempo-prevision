"""Tests for accuracy analysis (rtetempo-backed defaults)."""
from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.tempo_prevision.accuracy import (
    AccuracyAnalyzer,
    HorizonForecast,
    default_forecast_sensor_ids,
    resolve_actual_color_entities,
)
from custom_components.tempo_prevision.const import (
    DEFAULT_CURRENT_COLOR_ENTITY,
    DEFAULT_NEXT_COLOR_ENTITY,
)


def test_horizon_forecast_to_dict():
    """HorizonForecast serializes."""
    hf = HorizonForecast(color="rouge", result="✗")
    assert hf.to_dict() == {"color": "rouge", "result": "✗"}


def test_default_forecast_sensor_ids():
    """Default forecast entity IDs match migration names."""
    ids = default_forecast_sensor_ids()
    assert ids[2] == "sensor.rte_tempo_forecast_opendpe_j2"
    assert ids[7] == "sensor.rte_tempo_forecast_opendpe_j7"
    assert set(ids.keys()) == {2, 3, 4, 5, 6, 7}


@pytest.fixture
def analyzer():
    """Analyzer with mock hass."""
    return AccuracyAnalyzer(MagicMock())


def test_sunday_excluded(analyzer):
    """Sundays excluded from accuracy."""
    assert analyzer.is_excluded(datetime.date(2024, 12, 29)) is True


def test_holiday_excluded(analyzer):
    """Holidays excluded."""
    assert analyzer.is_excluded(datetime.date(2025, 12, 25)) is True


def test_weekday_not_excluded(analyzer):
    """Regular weekdays counted."""
    assert analyzer.is_excluded(datetime.date(2024, 12, 30)) is False


def test_compare_correct_incorrect(analyzer):
    """Compare returns ✓ / ✗ / -."""
    day = datetime.date(2024, 12, 30)
    assert analyzer._compare("bleu", "bleu", day) == "✓"
    assert analyzer._compare("rouge", "bleu", day) == "✗"
    assert analyzer._compare(None, "bleu", day) == "-"
    assert analyzer._compare("bleu", "bleu", datetime.date(2024, 12, 29)) == "-"


def test_calculate_horizon_accuracy(analyzer):
    """Horizon accuracy percentage."""
    matrix = [
        {"j2": {"result": "✓"}},
        {"j2": {"result": "✓"}},
        {"j2": {"result": "✗"}},
        {"j2": {"result": "-"}},
    ]
    assert analyzer.calculate_horizon_accuracy(matrix, 2) == pytest.approx(66.7)


def test_resolve_actual_color_defaults_to_rtetempo():
    """Without overrides, use hekmon/rtetempo entity IDs."""
    hass = MagicMock()
    current, nxt = resolve_actual_color_entities(hass)
    assert current == DEFAULT_CURRENT_COLOR_ENTITY
    assert nxt == DEFAULT_NEXT_COLOR_ENTITY


def test_resolve_actual_color_configured():
    """Configured entities win over defaults."""
    hass = MagicMock()
    current, nxt = resolve_actual_color_entities(
        hass,
        configured_current="sensor.my_tempo_today",
        configured_next="sensor.my_tempo_tomorrow",
    )
    assert current == "sensor.my_tempo_today"
    assert nxt == "sensor.my_tempo_tomorrow"


@pytest.mark.asyncio
async def test_analyze_empty_history():
    """Analyze with empty history returns zeros."""
    hass = MagicMock()
    analyzer = AccuracyAnalyzer(
        hass,
        current_color_entity="sensor.fake_current",
        next_color_entity=DEFAULT_NEXT_COLOR_ENTITY,
    )
    analyzer._get_raw_history = AsyncMock(return_value=[])
    hass.states.get.return_value = None
    result = await analyzer.analyze(days=7)
    assert result["accuracy_30d"] == 0.0
    assert result["past_matrix"] == []
    assert len(result["future_matrix"]) == 6
