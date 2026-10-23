"""Shared fixtures for tempo_prevision tests."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tempo_prevision.const import DOMAIN


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in tests."""
    return


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Tempo Prévision",
        data={},
        options={
            "accuracy_enabled": True,
            "current_color_entity": "",
            "next_color_entity": "",
        },
        unique_id=DOMAIN,
    )
