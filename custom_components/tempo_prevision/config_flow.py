"""Config flow for Tempo Prévision (no RTE credentials)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    OPTION_ACCURACY_ENABLED,
    OPTION_CURRENT_COLOR_ENTITY,
    OPTION_NEXT_COLOR_ENTITY,
)


def _options_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build options schema with optional entity selectors."""
    defaults = defaults or {}
    schema: dict[Any, Any] = {
        vol.Required(
            OPTION_ACCURACY_ENABLED,
            default=defaults.get(OPTION_ACCURACY_ENABLED, True),
        ): bool,
    }

    current = defaults.get(OPTION_CURRENT_COLOR_ENTITY) or None
    next_entity = defaults.get(OPTION_NEXT_COLOR_ENTITY) or None

    current_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )
    next_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )

    if current:
        schema[
            vol.Optional(
                OPTION_CURRENT_COLOR_ENTITY,
                default=current,
            )
        ] = current_selector
    else:
        schema[vol.Optional(OPTION_CURRENT_COLOR_ENTITY)] = current_selector

    if next_entity:
        schema[
            vol.Optional(
                OPTION_NEXT_COLOR_ENTITY,
                default=next_entity,
            )
        ] = next_selector
    else:
        schema[vol.Optional(OPTION_NEXT_COLOR_ENTITY)] = next_selector

    return vol.Schema(schema)


def _normalize_options(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize options; empty entity selectors become empty strings."""
    current = user_input.get(OPTION_CURRENT_COLOR_ENTITY) or ""
    next_entity = user_input.get(OPTION_NEXT_COLOR_ENTITY) or ""
    return {
        OPTION_ACCURACY_ENABLED: user_input.get(OPTION_ACCURACY_ENABLED, True),
        OPTION_CURRENT_COLOR_ENTITY: current,
        OPTION_NEXT_COLOR_ENTITY: next_entity,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tempo Prévision."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step — single instance, no credentials."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=_options_schema(),
            )

        return self.async_create_entry(
            title="Tempo Prévision",
            data={},
            options=_normalize_options(user_input),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Tempo Prévision."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=_normalize_options(user_input),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self.config_entry.options)),
        )
