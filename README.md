# Tempo Prévision

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Tests](https://github.com/rjullien/tempo-prevision/actions/workflows/tests.yml/badge.svg)](https://github.com/rjullien/tempo-prevision/actions/workflows/tests.yml)

Home Assistant custom integration: **Tempo color forecasts J+2..J+7** (Open DPE) and optional **forecast accuracy**.

Companion to the official RTE bridge [hekmon/rtetempo](https://github.com/hekmon/rtetempo) (v1.4.0+). This integration does **not** call the RTE API and needs **no credentials**.

> Upstream hekmon keeps `rtetempo` limited to official RTE data ([PR #66](https://github.com/hekmon/rtetempo/pull/66)). Forecast features that lived in [rjullien/rtetempo](https://github.com/rjullien/rtetempo) are extracted here so you can run pure upstream `rtetempo` again.

---

## Features

- Open DPE forecast coordinator (refresh at startup, daily 07:00, every 6 h)
- Sensors **J+2..J+7** (text + visual emoji), with Tempo rules:
  - Sundays → always blue (`indicator: D`)
  - French holidays treated like Saturdays (never red; `indicator: F`)
  - Saturday red → white with adjusted probability
- Optional **accuracy** sensor (recorder history, multi-horizon J-7..J-2)
  - Actual colors from configurable entities (default: auto-detect `sensor.rte_tempo_couleur_actuelle` / `sensor.rte_tempo_prochaine_couleur`)
  - If those entities are missing, accuracy is simply not created — **no hard dependency on rtetempo**

## Install (HACS)

1. HACS → Integrations → ⋮ → Custom repositories  
   URL: `https://github.com/rjullien/tempo-prevision` — category: Integration
2. Download **Tempo Prévision**
3. Restart Home Assistant
4. Settings → Devices & services → Add integration → **Tempo Prévision**

## Entities

| Suggested `entity_id` (migration-compatible) | Description |
|----------------------------------------------|-------------|
| `sensor.rte_tempo_forecast_opendpe_j2` … `_j7` | Forecast color (text) |
| `sensor.rte_tempo_forecast_opendpe_j2_emoji` … `_j7_emoji` | Forecast color (emoji) |
| `sensor.rte_tempo_forecast_accuracy` | Accuracy % (optional) |

`unique_id`s use the `tempo_prevision` domain. Suggested object IDs match the old fork names so dashboards/automations can keep working after migration (see [MIGRATION.md](MIGRATION.md)).

## Options

- **Enable forecast accuracy** — on/off
- **Actual / next-day color entities** — leave empty to auto-detect hekmon/rtetempo

## Examples

See [`examples/dashboard.yaml`](examples/dashboard.yaml) and [`examples/dashboard_basic.yaml`](examples/dashboard_basic.yaml).

## Development

```bash
pip install -r requirements-test.txt
pytest
```

## License

MIT — see [LICENSE](LICENSE).

Forecast logic adapted from contributions originally developed against the `rtetempo` fork; Open DPE data © [open-dpe.fr](https://open-dpe.fr).

---

## Français

Intégration Home Assistant autonome pour les **prévisions Tempo J+2..J+7** (Open DPE) et la **précision** des prévisions. Complément de [hekmon/rtetempo](https://github.com/hekmon/rtetempo) — aucun identifiant API RTE.

Procédure de migration depuis le fork `rjullien/rtetempo` : [MIGRATION.md](MIGRATION.md).
