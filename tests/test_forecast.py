"""Tests for forecast.py."""
from __future__ import annotations

import datetime
from typing import Any

import aiohttp
import pytest

from custom_components.tempo_prevision.forecast import async_fetch_opendpe_forecast


class MockResponse:
    """Mock aiohttp response."""

    def __init__(
        self,
        status: int = 200,
        json_data: Any = None,
        raise_on_json: Exception | None = None,
    ):
        self.status = status
        self._json_data = json_data
        self._raise_on_json = raise_on_json

    async def json(self):
        if self._raise_on_json:
            raise self._raise_on_json
        return self._json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockSession:
    """Mock aiohttp ClientSession."""

    def __init__(self, response: MockResponse | None = None, raise_on_get=None):
        self._response = response
        self._raise_on_get = raise_on_get

    def get(self, url: str, **kwargs):
        if self._raise_on_get:
            raise self._raise_on_get
        return self._response


@pytest.mark.asyncio
async def test_parse_valid_json():
    """Parse complete valid JSON."""
    data = [
        {"date": "2025-01-15", "couleur": "BLEU", "probability": 0.85},
        {"date": "2025-01-16", "couleur": "blanc", "probability": 0.72},
    ]
    result = await async_fetch_opendpe_forecast(MockSession(MockResponse(200, data)))
    assert len(result) == 2
    assert result[0].date == datetime.date(2025, 1, 15)
    assert result[0].color == "bleu"
    assert result[0].probability == 0.85
    assert result[0].source == "open_dpe"


@pytest.mark.asyncio
async def test_http_error_returns_empty():
    """HTTP errors return empty list."""
    result = await async_fetch_opendpe_forecast(MockSession(MockResponse(404)))
    assert result == []


@pytest.mark.asyncio
async def test_timeout_returns_empty():
    """Network/timeout errors return empty list."""
    result = await async_fetch_opendpe_forecast(
        MockSession(raise_on_get=aiohttp.ClientError("Timeout"))
    )
    assert result == []


@pytest.mark.asyncio
async def test_malformed_entry_skipped():
    """Malformed entries are skipped."""
    data = [
        {"date": "2025-01-15", "couleur": "bleu", "probability": 0.85},
        {"date": "invalid-date", "couleur": "blanc"},
        {"date": "2025-01-17", "couleur": "rouge", "probability": 0.45},
    ]
    result = await async_fetch_opendpe_forecast(MockSession(MockResponse(200, data)))
    assert len(result) == 2


@pytest.mark.asyncio
async def test_missing_probability_is_none():
    """Missing probability becomes None."""
    data = [{"date": "2025-01-15", "couleur": "bleu"}]
    result = await async_fetch_opendpe_forecast(MockSession(MockResponse(200, data)))
    assert result[0].probability is None
