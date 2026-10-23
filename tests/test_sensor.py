"""Tests for forecast sensor helpers and accuracy optional path."""
from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.tempo_prevision.const import (
    DOMAIN,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_WHITE_NAME,
)
from custom_components.tempo_prevision.forecast import ForecastDay
from custom_components.tempo_prevision.sensor import (
    get_color_emoji,
    get_color_icon,
    get_color_name,
)


def test_color_helpers():
    """Color helpers map known values."""
    assert get_color_name("bleu") == SENSOR_COLOR_BLUE_NAME
    assert get_color_name("blanc") == SENSOR_COLOR_WHITE_NAME
    assert get_color_name("rouge") == SENSOR_COLOR_RED_NAME
    assert get_color_emoji("bleu") == SENSOR_COLOR_BLUE_EMOJI
    assert get_color_emoji("blanc") == SENSOR_COLOR_WHITE_EMOJI
    assert get_color_emoji("rouge") == SENSOR_COLOR_RED_EMOJI
    assert get_color_icon("rouge") == "mdi:alert"
    assert get_color_name("???") == "inconnu"


def test_forecast_sensor_migration_entity_ids():
    """entity_id matches fork names for migration."""
    from custom_components.tempo_prevision.sensor import OpenDPEForecastSensor

    coordinator = MagicMock()
    coordinator.data = [
        ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.9),
        ForecastDay(date=datetime.date(2025, 1, 16), color="blanc", probability=0.8),
    ]

    sensor = OpenDPEForecastSensor.__new__(OpenDPEForecastSensor)
    OpenDPEForecastSensor.__init__(sensor, coordinator, index=1, visual=False)
    assert sensor._attr_unique_id == f"{DOMAIN}_forecast_opendpe_j2"
    assert sensor.entity_id == "sensor.rte_tempo_forecast_opendpe_j2"

    emoji = OpenDPEForecastSensor.__new__(OpenDPEForecastSensor)
    OpenDPEForecastSensor.__init__(emoji, coordinator, index=1, visual=True)
    assert emoji.entity_id == "sensor.rte_tempo_forecast_opendpe_j2_emoji"


def _sample_forecasts(n: int = 7) -> list[ForecastDay]:
    """Build n sample forecast days."""
    return [
        ForecastDay(
            date=datetime.date.today() + datetime.timedelta(days=i),
            color="bleu",
            probability=0.9,
        )
        for i in range(n)
    ]


@pytest.mark.asyncio
async def test_setup_skips_accuracy_without_source(hass, mock_config_entry):
    """Accuracy sensor is not created when no actual-color entity exists."""
    mock_config_entry.add_to_hass(hass)
    sample = _sample_forecasts()

    with (
        patch(
            "custom_components.tempo_prevision.forecast_coordinator.async_get_clientsession",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.tempo_prevision.forecast_coordinator.async_track_time_change",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.tempo_prevision.forecast_coordinator.async_fetch_opendpe_forecast",
            new=AsyncMock(return_value=sample),
        ),
        patch(
            "custom_components.tempo_prevision.sensor.resolve_actual_color_entities",
            return_value=(None, None),
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_ids = hass.states.async_entity_ids("sensor")
        forecast_ids = [e for e in entity_ids if "opendpe" in e]
        accuracy_ids = [e for e in entity_ids if "accuracy" in e]
        assert "sensor.rte_tempo_forecast_opendpe_j2" in entity_ids
        assert len(forecast_ids) >= 6
        assert accuracy_ids == []

        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_setup_creates_accuracy_when_source_present(hass, mock_config_entry):
    """Accuracy sensor is created when actual-color entity resolves."""
    mock_config_entry.add_to_hass(hass)
    sample = _sample_forecasts()

    with (
        patch(
            "custom_components.tempo_prevision.forecast_coordinator.async_get_clientsession",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.tempo_prevision.forecast_coordinator.async_track_time_change",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.tempo_prevision.forecast_coordinator.async_fetch_opendpe_forecast",
            new=AsyncMock(return_value=sample),
        ),
        patch(
            "custom_components.tempo_prevision.sensor.resolve_actual_color_entities",
            return_value=("sensor.rte_tempo_couleur_actuelle", None),
        ),
        patch(
            "custom_components.tempo_prevision.sensor.AccuracyAnalyzer.analyze",
            new=AsyncMock(
                return_value={
                    "accuracy_30d": 80.0,
                    "past_matrix": [],
                    "future_matrix": [],
                }
            ),
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_ids = hass.states.async_entity_ids("sensor")
        assert "sensor.rte_tempo_forecast_accuracy" in entity_ids

        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
