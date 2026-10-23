"""Tests for ForecastCoordinator."""
from __future__ import annotations

import datetime
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.tempo_prevision.forecast import ForecastDay


@pytest.fixture
def mock_hass():
    """Minimal hass mock."""
    hass = MagicMock()
    hass.data = {}
    return hass


@patch("custom_components.tempo_prevision.forecast_coordinator.async_get_clientsession")
@patch("custom_components.tempo_prevision.forecast_coordinator.async_track_time_change")
def test_update_interval_and_cleanup(mock_track, mock_session, mock_hass):
    """Coordinator uses 6h interval and cleans up time listener."""
    cancel = MagicMock()
    mock_track.return_value = cancel
    mock_session.return_value = MagicMock()

    from custom_components.tempo_prevision.forecast_coordinator import (
        ForecastCoordinator,
    )

    coordinator = ForecastCoordinator(mock_hass)
    assert coordinator.update_interval == timedelta(hours=6)
    mock_track.assert_called_once()

    coordinator.async_unload()
    cancel.assert_called_once()
    coordinator.async_unload()  # second call is noop
    assert cancel.call_count == 1


@patch("custom_components.tempo_prevision.forecast_coordinator.async_get_clientsession")
@patch("custom_components.tempo_prevision.forecast_coordinator.async_track_time_change")
@pytest.mark.asyncio
async def test_async_update_applies_rules(mock_track, mock_session, mock_hass):
    """Update fetches forecasts and applies Tempo rules."""
    mock_track.return_value = MagicMock()
    mock_session.return_value = MagicMock()

    from custom_components.tempo_prevision.forecast_coordinator import (
        ForecastCoordinator,
    )

    raw = [
        ForecastDay(
            date=datetime.date(2025, 1, 12),  # Sunday
            color="rouge",
            probability=0.9,
        )
    ]

    with patch(
        "custom_components.tempo_prevision.forecast_coordinator.async_fetch_opendpe_forecast",
        new=AsyncMock(return_value=raw),
    ):
        coordinator = ForecastCoordinator(mock_hass)
        data = await coordinator._async_update_data()

    assert len(data) == 1
    assert data[0].color == "bleu"
    assert data[0].indicator == "D"


@patch("custom_components.tempo_prevision.forecast_coordinator.async_get_clientsession")
@patch("custom_components.tempo_prevision.forecast_coordinator.async_track_time_change")
@pytest.mark.asyncio
async def test_async_update_raises_update_failed(mock_track, mock_session, mock_hass):
    """Unexpected errors become UpdateFailed."""
    mock_track.return_value = MagicMock()
    mock_session.return_value = MagicMock()

    from custom_components.tempo_prevision.forecast_coordinator import (
        ForecastCoordinator,
    )

    with patch(
        "custom_components.tempo_prevision.forecast_coordinator.async_fetch_opendpe_forecast",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        coordinator = ForecastCoordinator(mock_hass)
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
