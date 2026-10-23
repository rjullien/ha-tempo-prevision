"""Constants for the Tempo Prévision integration."""
from __future__ import annotations

DOMAIN = "tempo_prevision"

# Config / options
OPTION_ACCURACY_ENABLED = "accuracy_enabled"
OPTION_CURRENT_COLOR_ENTITY = "current_color_entity"
OPTION_NEXT_COLOR_ENTITY = "next_color_entity"

# Default hekmon/rtetempo entity IDs (auto-detected when present)
DEFAULT_CURRENT_COLOR_ENTITY = "sensor.rte_tempo_couleur_actuelle"
DEFAULT_NEXT_COLOR_ENTITY = "sensor.rte_tempo_prochaine_couleur"

# Suggested object_ids matching rjullien/rtetempo fork entity_ids (migration)
SUGGESTED_FORECAST_OBJECT_ID = "rte_tempo_forecast_opendpe_j{day}"
SUGGESTED_FORECAST_EMOJI_OBJECT_ID = "rte_tempo_forecast_opendpe_j{day}_emoji"
SUGGESTED_ACCURACY_OBJECT_ID = "rte_tempo_forecast_accuracy"

# Device
DEVICE_NAME = "Tempo Prévision"
DEVICE_MANUFACTURER = "Open DPE"
DEVICE_MODEL = "Prévisions Tempo J+2..J+7"

# Color display
SENSOR_COLOR_BLUE_NAME = "Bleu"
SENSOR_COLOR_BLUE_EMOJI = "🔵"
SENSOR_COLOR_WHITE_NAME = "Blanc"
SENSOR_COLOR_WHITE_EMOJI = "⚪"
SENSOR_COLOR_RED_NAME = "Ro" + "uge"  # codespell workaround
SENSOR_COLOR_RED_EMOJI = "🔴"
SENSOR_COLOR_UNKNOWN_NAME = "inconnu"
SENSOR_COLOR_UNKNOWN_EMOJI = "❓"

# Forecast window: OpenDPE returns ~7 days; J+1 is official RTE → sensors for J+2..J+7
NUM_FORECAST_DAYS = 7
FORECAST_START_INDEX = 1  # skip index 0 (J+1)

ATTRIBUTION = "Données Tempo : Open DPE (https://open-dpe.fr)"
