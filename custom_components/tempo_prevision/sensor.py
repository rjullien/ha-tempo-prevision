"""Sensors for Tempo Prévision: OpenDPE J+2..J+7 and optional accuracy."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .accuracy import AccuracyAnalyzer, resolve_actual_color_entities
from .const import (
    ATTRIBUTION,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    FORECAST_START_INDEX,
    NUM_FORECAST_DAYS,
    OPTION_ACCURACY_ENABLED,
    OPTION_CURRENT_COLOR_ENTITY,
    OPTION_NEXT_COLOR_ENTITY,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_UNKNOWN_EMOJI,
    SENSOR_COLOR_UNKNOWN_NAME,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_WHITE_NAME,
    SUGGESTED_ACCURACY_OBJECT_ID,
    SUGGESTED_FORECAST_EMOJI_OBJECT_ID,
    SUGGESTED_FORECAST_OBJECT_ID,
)
from .forecast import ForecastDay
from .forecast_coordinator import ForecastCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


def get_color_emoji(value: str) -> str:
    """Return emoji for a Tempo color."""
    if value == "rouge":
        return SENSOR_COLOR_RED_EMOJI
    if value == "blanc":
        return SENSOR_COLOR_WHITE_EMOJI
    if value == "bleu":
        return SENSOR_COLOR_BLUE_EMOJI
    return SENSOR_COLOR_UNKNOWN_EMOJI


def get_color_name(value: str) -> str:
    """Return display name for a Tempo color."""
    if value == "rouge":
        return SENSOR_COLOR_RED_NAME
    if value == "blanc":
        return SENSOR_COLOR_WHITE_NAME
    if value == "bleu":
        return SENSOR_COLOR_BLUE_NAME
    return SENSOR_COLOR_UNKNOWN_NAME


def get_color_icon(value: str) -> str:
    """Return mdi icon for a Tempo color."""
    if value == "rouge":
        return "mdi:alert"
    if value == "blanc":
        return "mdi:information-outline"
    if value == "bleu":
        return "mdi:check-bold"
    return "mdi:palette"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tempo Prévision sensors from a config entry."""
    coordinator: ForecastCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities: list[SensorEntity] = []

    for index in range(FORECAST_START_INDEX, NUM_FORECAST_DAYS):
        entities.append(OpenDPEForecastSensor(coordinator, index, visual=False))
        entities.append(OpenDPEForecastSensor(coordinator, index, visual=True))

    accuracy_enabled = config_entry.options.get(OPTION_ACCURACY_ENABLED, True)
    if accuracy_enabled:
        configured_current = config_entry.options.get(OPTION_CURRENT_COLOR_ENTITY) or None
        configured_next = config_entry.options.get(OPTION_NEXT_COLOR_ENTITY) or None
        current, next_entity = resolve_actual_color_entities(
            hass,
            configured_current=configured_current,
            configured_next=configured_next,
        )
        if current:
            entities.append(
                TempoAccuracySensor(
                    hass,
                    config_entry.entry_id,
                    current_color_entity=current,
                    next_color_entity=next_entity,
                )
            )
            _LOGGER.info(
                "Accuracy sensor enabled (actual color: %s, next: %s)",
                current,
                next_entity,
            )
        else:
            _LOGGER.info(
                "Accuracy sensor skipped: no actual-color source entity "
                "(install hekmon/rtetempo or set the option manually)"
            )

    async_add_entities(entities, True)


class OpenDPEForecastSensor(CoordinatorEntity[ForecastCoordinator], SensorEntity):
    """OpenDPE forecast sensor (text or visual version)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ForecastCoordinator, index: int, visual: bool
    ) -> None:
        """Initialize the forecast sensor."""
        super().__init__(coordinator)
        self.index = index
        self.visual = visual
        day = index + 1  # J2..J7

        if visual:
            self._attr_name = f"OpenDPE J{day} (visuel)"
            self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{day}_emoji"
            # Force migration-compatible entity_id (HA 2024+ derives object_id from name otherwise)
            self.entity_id = (
                f"sensor.{SUGGESTED_FORECAST_EMOJI_OBJECT_ID.format(day=day)}"
            )
            self._attr_options = [
                SENSOR_COLOR_BLUE_EMOJI,
                SENSOR_COLOR_WHITE_EMOJI,
                SENSOR_COLOR_RED_EMOJI,
                SENSOR_COLOR_UNKNOWN_EMOJI,
            ]
            self._attr_icon = "mdi:palette"
        else:
            self._attr_name = f"OpenDPE J{day}"
            self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{day}"
            self.entity_id = (
                f"sensor.{SUGGESTED_FORECAST_OBJECT_ID.format(day=day)}"
            )
            self._attr_options = [
                SENSOR_COLOR_BLUE_NAME,
                SENSOR_COLOR_WHITE_NAME,
                SENSOR_COLOR_RED_NAME,
                SENSOR_COLOR_UNKNOWN_NAME,
            ]
            self._attr_icon = "mdi:calendar"

        self._attr_native_value: Optional[str] = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info shared by all forecast sensors."""
        return DeviceInfo(
            identifiers={(DOMAIN, "forecast")},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return True if coordinator has data for this index."""
        data = self.coordinator.data
        return data is not None and len(data) > self.index

    async def async_added_to_hass(self) -> None:
        """Register coordinator listener and apply current data immediately."""
        await super().async_added_to_hass()
        self._apply_forecast()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._apply_forecast()
        self.async_write_ha_state()

    def _apply_forecast(self) -> None:
        """Update native value and attributes from coordinator data."""
        data = self.coordinator.data

        if not data or len(data) <= self.index:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        forecast: ForecastDay = data[self.index]
        color = forecast.color.lower()

        if color not in ["bleu", "blanc", "rouge"]:
            color = "inconnu"

        if self.visual:
            self._attr_native_value = get_color_emoji(color)
            self._attr_icon = get_color_icon(color)
        else:
            self._attr_native_value = get_color_name(color)

        if forecast.indicator:
            self._attr_extra_state_attributes = {
                "date": forecast.date.isoformat(),
                "indicator": forecast.indicator,
                "attribution": ATTRIBUTION,
            }
        else:
            self._attr_extra_state_attributes = {
                "date": forecast.date.isoformat(),
                "probability": forecast.probability,
                "attribution": ATTRIBUTION,
            }


class TempoAccuracySensor(SensorEntity):
    """Sensor showing forecast accuracy percentage (optional companion)."""

    _attr_has_entity_name = True
    _attr_name = "Forecast Accuracy"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:chart-donut"
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_id: str,
        *,
        current_color_entity: str,
        next_color_entity: str | None,
    ) -> None:
        """Initialize the accuracy sensor."""
        self.hass = hass
        self._config_id = config_id
        self._attr_unique_id = f"{DOMAIN}_{config_id}_forecast_accuracy"
        self.entity_id = f"sensor.{SUGGESTED_ACCURACY_OBJECT_ID}"
        self._analyzer = AccuracyAnalyzer(
            hass,
            current_color_entity=current_color_entity,
            next_color_entity=next_color_entity,
        )
        self._data: dict[str, Any] = {}
        self._attr_available = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, "forecast")},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @property
    def native_value(self) -> float | None:
        """Return the accuracy percentage."""
        return self._data.get("accuracy_30d")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return self._data

    async def async_update(self) -> None:
        """Update accuracy data from history (requires recorder)."""
        try:
            self._data = await self._analyzer.analyze(days=30)
            self._attr_available = True
        except Exception as err:
            _LOGGER.error("Error analyzing forecast accuracy: %s", err)
            self._data = {}
            self._attr_available = False
