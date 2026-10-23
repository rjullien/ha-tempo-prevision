"""Tests for Tempo Prévision config flow."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tempo_prevision.const import (
    DOMAIN,
    OPTION_ACCURACY_ENABLED,
    OPTION_CURRENT_COLOR_ENTITY,
    OPTION_NEXT_COLOR_ENTITY,
)


@pytest.mark.asyncio
async def test_user_form_creates_entry(hass):
    """Config flow creates a single entry without credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.tempo_prevision.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                OPTION_ACCURACY_ENABLED: True,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Tempo Prévision"
    assert result2["data"] == {}
    assert result2["options"][OPTION_ACCURACY_ENABLED] is True


@pytest.mark.asyncio
async def test_abort_if_already_configured(hass):
    """Only one config entry is allowed."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_options_flow(hass, mock_config_entry):
    """Options flow updates accuracy settings."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.tempo_prevision.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        assert result["type"] is FlowResultType.FORM

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                OPTION_ACCURACY_ENABLED: False,
                OPTION_CURRENT_COLOR_ENTITY: "sensor.custom_color",
            },
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"][OPTION_ACCURACY_ENABLED] is False
    assert result2["data"][OPTION_CURRENT_COLOR_ENTITY] == "sensor.custom_color"
    assert result2["data"][OPTION_NEXT_COLOR_ENTITY] == ""
