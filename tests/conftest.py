"""Shared fixtures for tempo_prevision tests."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tempo_prevision.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_STUB_SRC = Path(__file__).resolve().parent / "stubs" / "rtetempo"
_STUB_DST = _REPO_ROOT / "custom_components" / "rtetempo"


@pytest.fixture(scope="session", autouse=True)
def install_rtetempo_stub():
    """Install a minimal rtetempo custom_component so the dependency can load."""
    if _STUB_DST.exists():
        yield
        return

    shutil.copytree(_STUB_SRC, _STUB_DST)
    try:
        yield
    finally:
        shutil.rmtree(_STUB_DST, ignore_errors=True)


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
