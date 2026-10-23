"""Accuracy analysis for Tempo forecasts.

Compares forecast predictions to actual colors. Actual-color source entities
are configurable (default: hekmon/rtetempo sensors when present).
Sundays and French holidays are excluded from calculations.
"""
from __future__ import annotations

import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .const import (
    DEFAULT_CURRENT_COLOR_ENTITY,
    DEFAULT_NEXT_COLOR_ENTITY,
    SUGGESTED_FORECAST_OBJECT_ID,
)
from .tempo_rules import is_french_holiday

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def default_forecast_sensor_ids() -> Dict[int, str]:
    """Entity IDs for J+2..J+7 text forecast sensors (migration-compatible)."""
    return {
        day: f"sensor.{SUGGESTED_FORECAST_OBJECT_ID.format(day=day)}"
        for day in range(2, 8)
    }


@dataclass
class HorizonForecast:
    """Forecast at a specific horizon."""

    color: Optional[str] = None
    result: str = "-"

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {"color": self.color, "result": self.result}


class AccuracyAnalyzer:
    """Analyzes forecast accuracy via Home Assistant recorder history."""

    def __init__(
        self,
        hass: "HomeAssistant",
        *,
        forecast_sensors: Optional[Dict[int, str]] = None,
        current_color_entity: str = DEFAULT_CURRENT_COLOR_ENTITY,
        next_color_entity: Optional[str] = DEFAULT_NEXT_COLOR_ENTITY,
    ) -> None:
        """Initialize the analyzer with configurable source entities."""
        self.hass = hass
        self.forecast_sensors = forecast_sensors or default_forecast_sensor_ids()
        self.current_color_entity = current_color_entity
        self.next_color_entity = next_color_entity

    def is_excluded(self, date: datetime.date) -> bool:
        """Check if date should be excluded from accuracy calculation."""
        if date.weekday() == 6:  # Sunday
            return True
        return is_french_holiday(date)

    async def _get_raw_history(
        self,
        entity_id: str,
        days: int = 30,
    ) -> List[Any]:
        """Get raw state history for an entity from HA recorder."""
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import get_significant_states

        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(days=days + 10)

        try:
            states = await get_instance(self.hass).async_add_executor_job(
                get_significant_states,
                self.hass,
                start_time,
                end_time,
                [entity_id],
            )
            return states.get(entity_id, [])
        except Exception as err:
            _LOGGER.error("Error getting history for %s: %s", entity_id, err)
            return []

    async def get_forecast_history_by_target_date(
        self,
        days: int = 30,
    ) -> Dict[str, Dict[int, str]]:
        """Get forecast history organized by target date and horizon."""
        result: Dict[str, Dict[int, str]] = defaultdict(dict)

        for horizon, sensor_id in self.forecast_sensors.items():
            states = await self._get_raw_history(sensor_id, days)

            by_target_and_forecast_date: Dict[str, Dict[str, tuple]] = defaultdict(
                dict
            )

            for state in states:
                if state.state in ("unknown", "unavailable", None):
                    continue

                color = state.state.lower()
                if color not in ("bleu", "blanc", "rouge"):
                    continue

                attrs = state.attributes or {}
                target_date = attrs.get("date")
                if not target_date:
                    continue

                forecast_date = state.last_changed.strftime("%Y-%m-%d")
                forecast_time = state.last_changed

                existing = by_target_and_forecast_date[target_date].get(forecast_date)
                if existing is None or forecast_time > existing[1]:
                    by_target_and_forecast_date[target_date][forecast_date] = (
                        color,
                        forecast_time,
                    )

            for target_date, forecasts_by_day in by_target_and_forecast_date.items():
                try:
                    target = datetime.date.fromisoformat(target_date)
                except ValueError:
                    continue

                expected_forecast_date = (
                    target - datetime.timedelta(days=horizon)
                ).isoformat()

                if expected_forecast_date in forecasts_by_day:
                    result[target_date][horizon] = forecasts_by_day[
                        expected_forecast_date
                    ][0]

        return dict(result)

    async def get_actual_colors(self, days: int = 30) -> Dict[str, str]:
        """Get actual colors by date from history (+ tomorrow if next entity set)."""
        states = await self._get_raw_history(self.current_color_entity, days)

        result: Dict[str, str] = {}
        for state in states:
            if state.state in ("unknown", "unavailable", None):
                continue

            color = state.state.lower()
            if color not in ("bleu", "blanc", "rouge"):
                continue

            date_str = state.last_changed.strftime("%Y-%m-%d")
            result[date_str] = color

        if self.next_color_entity:
            tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            next_color_state = self.hass.states.get(self.next_color_entity)
            if next_color_state and next_color_state.state not in (
                "unknown",
                "unavailable",
                None,
            ):
                color = next_color_state.state.lower()
                if color in ("bleu", "blanc", "rouge"):
                    result[tomorrow] = color

        return result

    def _compare(
        self, predicted: Optional[str], actual: str, date: datetime.date
    ) -> str:
        """Compare prediction to actual and return result symbol."""
        if predicted is None:
            return "-"
        if self.is_excluded(date):
            return "-"
        return "✓" if predicted == actual else "✗"

    async def build_past_matrix(self, days: int = 30) -> List[dict]:
        """Build the past accuracy matrix (up to tomorrow if J+1 known)."""
        forecasts = await self.get_forecast_history_by_target_date(days)
        actuals = await self.get_actual_colors(days)

        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        matrix = []

        for date_str, actual in sorted(actuals.items(), reverse=True):
            try:
                date = datetime.date.fromisoformat(date_str)
            except ValueError:
                continue

            if date > tomorrow:
                continue

            if (today - date).days > days:
                continue

            row: dict = {
                "date": date_str,
                "actual": actual,
            }

            date_forecasts = forecasts.get(date_str, {})
            for h in range(7, 1, -1):
                predicted = date_forecasts.get(h)
                result = self._compare(predicted, actual, date)
                row[f"j{h}"] = {"color": predicted, "result": result}

            matrix.append(row)

        return matrix

    async def build_future_matrix(self) -> List[dict]:
        """Build the future forecast matrix (no actual column)."""
        today = datetime.date.today()
        forecasts = await self.get_forecast_history_by_target_date(days=14)
        matrix = []

        for days_ahead in range(2, 8):
            target_date = today + datetime.timedelta(days=days_ahead)
            date_str = target_date.isoformat()
            row: dict = {"date": date_str}
            date_forecasts = forecasts.get(date_str, {})

            for horizon in range(7, 1, -1):
                forecast_date = target_date - datetime.timedelta(days=horizon)
                if forecast_date <= today:
                    color = date_forecasts.get(horizon)
                    row[f"j{horizon}"] = {"color": color}
                else:
                    row[f"j{horizon}"] = {"color": None}

            matrix.append(row)

        return matrix

    def calculate_horizon_accuracy(
        self,
        past_matrix: List[dict],
        horizon: int,
    ) -> float:
        """Calculate accuracy percentage for a specific horizon."""
        key = f"j{horizon}"
        valid = []
        correct = 0

        for row in past_matrix:
            h_data = row.get(key, {})
            result = h_data.get("result", "-")

            if result != "-":
                valid.append(result)
                if result == "✓":
                    correct += 1

        if not valid:
            return 0.0

        return round((correct / len(valid)) * 100, 1)

    async def analyze(self, days: int = 30) -> dict:
        """Run full analysis and return results."""
        past_matrix = await self.build_past_matrix(days)
        future_matrix = await self.build_future_matrix()

        horizon_accuracy = {}
        for h in range(2, 8):
            horizon_accuracy[f"accuracy_j{h}"] = self.calculate_horizon_accuracy(
                past_matrix, h
            )

        total_correct = 0
        total_incorrect = 0
        total_excluded = 0

        for row in past_matrix:
            for h in range(2, 8):
                result = row.get(f"j{h}", {}).get("result", "-")
                if result == "✓":
                    total_correct += 1
                elif result == "✗":
                    total_incorrect += 1
                elif result == "-":
                    total_excluded += 1

        accuracy_30d = self.calculate_horizon_accuracy(past_matrix, 2)

        cutoff = datetime.date.today() - datetime.timedelta(days=7)
        recent_matrix = [
            r
            for r in past_matrix
            if datetime.date.fromisoformat(r["date"]) >= cutoff
        ]
        accuracy_7d = (
            self.calculate_horizon_accuracy(recent_matrix, 2) if recent_matrix else 0.0
        )

        return {
            "accuracy_30d": accuracy_30d,
            "accuracy_7d": accuracy_7d,
            **horizon_accuracy,
            "total_days": len(past_matrix),
            "correct_predictions": total_correct,
            "incorrect_predictions": total_incorrect,
            "excluded_predictions": total_excluded,
            "past_matrix": past_matrix,
            "future_matrix": future_matrix,
            "current_color_entity": self.current_color_entity,
            "next_color_entity": self.next_color_entity,
        }


def resolve_actual_color_entities(
    hass: "HomeAssistant",
    *,
    configured_current: Optional[str] = None,
    configured_next: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve actual-color source entities.

    Returns (current, next). current is None if unavailable → accuracy skipped.
    """
    current = (configured_current or "").strip() or None
    next_entity = (configured_next or "").strip() or None

    if current is None:
        state = hass.states.get(DEFAULT_CURRENT_COLOR_ENTITY)
        if state is not None and state.state not in ("unknown", "unavailable"):
            current = DEFAULT_CURRENT_COLOR_ENTITY
        elif hass.states.get(DEFAULT_CURRENT_COLOR_ENTITY) is not None:
            # Entity exists but may be temporarily unavailable — still use it
            current = DEFAULT_CURRENT_COLOR_ENTITY

    if next_entity is None:
        if hass.states.get(DEFAULT_NEXT_COLOR_ENTITY) is not None:
            next_entity = DEFAULT_NEXT_COLOR_ENTITY

    return current, next_entity
