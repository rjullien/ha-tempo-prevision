"""Minimal rtetempo stub for pytest (tempo_prevision depends on rtetempo)."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "rtetempo"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the stub integration."""
    hass.data.setdefault(DOMAIN, {})
    return True
