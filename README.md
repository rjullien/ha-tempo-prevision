# Tempo Prévision

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Tests](https://github.com/rjullien/ha-tempo-prevision/actions/workflows/tests.yml/badge.svg)](https://github.com/rjullien/ha-tempo-prevision/actions/workflows/tests.yml)

Home Assistant custom integration: **Tempo color forecasts J+2..J+7** (Open DPE) and optional **forecast accuracy**.

Companion to the official RTE bridge [hekmon/rtetempo](https://github.com/hekmon/rtetempo) (v1.4.0+). This integration does **not** call the RTE API and needs **no credentials**.

> Upstream hekmon keeps `rtetempo` limited to official RTE data ([PR #66](https://github.com/hekmon/rtetempo/pull/66)). Forecast features that lived in [rjullien/rtetempo](https://github.com/rjullien/rtetempo) are extracted here so you can run pure upstream `rtetempo` again.

---

## Prerequisites / Dependencies

**Required:** install and configure **[hekmon/rtetempo](https://github.com/hekmon/rtetempo)** first (HACS → Integration).

- Domain dependency: `rtetempo` (declared in `manifest.json`)
- Accuracy defaults to `sensor.rte_tempo_couleur_actuelle` and `sensor.rte_tempo_prochaine_couleur`

## Features

- Open DPE forecast coordinator (refresh at startup, daily 07:00, every 6 h)
- Sensors **J+2..J+7** (text + visual), with Tempo rules:
  - Sundays → always blue (`indicator: D`)
  - French holidays treated like Saturdays (never red; `indicator: F`)
  - Saturday red → white with adjusted probability
- Optional **accuracy** sensor (recorder history, multi-horizon J-7..J-2)
  - Actual colors default to hekmon/rtetempo sensors (overridable in options)

## Install (HACS)

1. Install **[RTE Tempo (hekmon/rtetempo)](https://github.com/hekmon/rtetempo)** and configure your RTE API credentials
2. HACS → Integrations → ⋮ → Custom repositories  
   URL: `https://github.com/rjullien/ha-tempo-prevision` — category: Integration
3. Download **Tempo Prévision**
4. Restart Home Assistant
5. Settings → Devices & services → Add integration → **Tempo Prévision**

## Entities

| Suggested `entity_id` (migration-compatible) | Description |
|----------------------------------------------|-------------|
| `sensor.rte_tempo_forecast_opendpe_j2` … `_j7` | Forecast color (text) |
| `sensor.rte_tempo_forecast_opendpe_j2_visuel` … `_j7_visuel` | Forecast color (visual) |
| `sensor.rte_tempo_forecast_accuracy` | Accuracy % (optional) |

`unique_id`s use the `tempo_prevision` domain (fork used `rtetempo_forecast_opendpe_jN` / `…_emoji` and `rtetempo_<entry_id>_forecast_accuracy`). Suggested object IDs match PROD entity_ids so dashboards/automations keep working after migration (see [MIGRATION.md](MIGRATION.md)).

## Options

- **Enable forecast accuracy** — on/off
- **Actual / next-day color entities** — leave empty to use hekmon/rtetempo defaults

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

### Prérequis / Dépendances

**Obligatoire :** installer et configurer d’abord **[hekmon/rtetempo](https://github.com/hekmon/rtetempo)** (HACS).

- Dépendance de domaine : `rtetempo` (déclarée dans `manifest.json`)
- La précision utilise par défaut `sensor.rte_tempo_couleur_actuelle` et `sensor.rte_tempo_prochaine_couleur`

Intégration Home Assistant pour les **prévisions Tempo J+2..J+7** (Open DPE) et la **précision** des prévisions. Complément de [hekmon/rtetempo](https://github.com/hekmon/rtetempo) — aucun identifiant API RTE.

Procédure de migration depuis le fork `rjullien/rtetempo` : [MIGRATION.md](MIGRATION.md).
