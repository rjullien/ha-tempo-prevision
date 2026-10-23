# Migration : fork `rjullien/rtetempo` → `tempo_prevision` + upstream `hekmon/rtetempo`

Objectif : retrouver un `rtetempo` officiel (v1.4.0) **sans** prévisions Open DPE, et déplacer ces prévisions vers **Tempo Prévision** ([ha-tempo-prevision](https://github.com/rjullien/ha-tempo-prevision)).

**Prérequis :** `tempo_prevision` **dépend** de `rtetempo` ([hekmon/rtetempo](https://github.com/hekmon/rtetempo)). Les deux dépôts HACS (fork et upstream) installent dans `custom_components/rtetempo` — ils ne peuvent pas coexister.

## Mapping des entités

| Ancien (fork PROD) | Nouveau (tempo_prevision) | Notes |
|--------------------|---------------------------|--------|
| `sensor.rte_tempo_forecast_opendpe_j2` … `_j7` | mêmes `entity_id` | Renommer si HA a ajouté un suffixe `_2` pendant la coexistence |
| `sensor.rte_tempo_forecast_opendpe_j2_visuel` … `_j7_visuel` | mêmes `entity_id` | Les unique_ids du fork étaient `…_emoji` ; les entity_ids PROD sont `…_visuel` |
| `sensor.rte_tempo_forecast_accuracy` | même `entity_id` | Fork unique_id : `rtetempo_<entry_id>_forecast_accuracy` |
| Capteurs RTE officiels (`couleur_actuelle`, etc.) | inchangés via hekmon/rtetempo | |

Les `unique_id` changent (`rtetempo_…` → `tempo_prevision_…`) : ce n’est **pas** un problème tant que les `entity_id` utilisés dans dashboards/automations restent les mêmes.

## Procédure recommandée

### 1. Installer / conserver hekmon/rtetempo v1.4.0

1. Dans HACS, retirer le dépôt **rjullien/rtetempo** (fork) si présent
2. Installer **[hekmon/rtetempo](https://github.com/hekmon/rtetempo)** v1.4.0+ (upstream sans Open DPE)
3. Redémarrer Home Assistant et vérifier les capteurs RTE (`couleur_actuelle`, `prochaine_couleur`, …)

Les capteurs Open DPE du fork disparaissent (ou deviennent orphelins).

### 2. Installer Tempo Prévision (HACS)

1. Ajouter le dépôt custom `https://github.com/rjullien/ha-tempo-prevision`
2. Télécharger **Tempo Prévision**, redémarrer HA
3. Ajouter l’intégration **Tempo Prévision** (UI) — nécessite `rtetempo` déjà chargé
4. Noter les `entity_id` créés (s’ils ont un suffixe `_2`, c’est normal tant que des orphelins existent)

### 3. Nettoyer les entités orphelines

1. Paramètres → Appareils et services → Entités
2. Filtrer les indisponibles / orphelines liées à `rte_tempo_forecast_*` de l’ancien domaine `rtetempo`
3. Les supprimer

### 4. Aligner les `entity_id` (si besoin)

Si Tempo Prévision a créé par exemple `sensor.rte_tempo_forecast_opendpe_j2_2` :

1. Ouvrir l’entité → Paramètres
2. Renommer l’identifiant en `sensor.rte_tempo_forecast_opendpe_j2` (idem pour j3…j7, `_visuel`, accuracy)
3. Enregistrer

Les dashboards / automations qui pointaient déjà vers les anciens IDs refonctionnent sans modification.

### 5. Vérifier

- États J+2..J+7 mis à jour (couleur + attributs `date` / `probability` ou `indicator`)
- Capteur accuracy présent (par défaut branché sur les capteurs rtetempo)
- Dashboards `examples/` et vos cartes Lovelace

## Options accuracy

Dans les options de Tempo Prévision :

- **Activer la précision** : oui/non
- **Entité couleur réelle** / **lendemain** : laisser vide pour les défauts rtetempo ; sinon choisir d’autres capteurs

## Rollback

Réinstaller le fork `rjullien/rtetempo` et désactiver Tempo Prévision. Attention : conflit de chemin `custom_components/rtetempo` — ne garder qu’une seule installation `rtetempo` à la fois.
