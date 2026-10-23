# Migration : fork `rjullien/rtetempo` → `tempo_prevision` + upstream `hekmon/rtetempo`

Objectif : retrouver un `rtetempo` officiel (v1.4.0) **sans** prévisions Open DPE, et déplacer ces prévisions vers **Tempo Prévision**.

Les deux dépôts HACS (fork et upstream) installent dans `custom_components/rtetempo` — ils ne peuvent pas coexister. D’où l’ordre ci-dessous.

## Mapping des entités

| Ancien (fork) | Nouveau (tempo_prevision) | Notes |
|---------------|---------------------------|--------|
| `sensor.rte_tempo_forecast_opendpe_j2` … `_j7` | mêmes `entity_id` suggérés | Renommer si HA a ajouté un suffixe `_2` pendant la coexistence |
| `sensor.rte_tempo_forecast_opendpe_j2_emoji` … `_j7_emoji` | mêmes `entity_id` suggérés | idem |
| `sensor.rte_tempo_forecast_accuracy` | même `entity_id` suggéré | Créé seulement si une source de couleur réelle est dispo |
| Capteurs RTE officiels (`couleur_actuelle`, etc.) | inchangés via hekmon/rtetempo | |

Les `unique_id` changent (`rtetempo_…` → `tempo_prevision_…`) : ce n’est **pas** un problème tant que les `entity_id` utilisés dans dashboards/automations restent les mêmes.

## Procédure recommandée

### 1. Installer Tempo Prévision (HACS)

1. Ajouter le dépôt custom `https://github.com/rjullien/tempo-prevision`
2. Télécharger **Tempo Prévision**, redémarrer HA
3. Ajouter l’intégration **Tempo Prévision** (UI)
4. Noter les `entity_id` créés (s’ils ont un suffixe `_2`, c’est normal tant que le fork est encore là)

### 2. Remplacer le fork par hekmon/rtetempo v1.4.0

1. Dans HACS, retirer / désinstaller le dépôt **rjullien/rtetempo** (fork)
2. Ajouter / réinstaller **[hekmon/rtetempo](https://github.com/hekmon/rtetempo)** en version **v1.4.0** (ou plus récente upstream sans Open DPE)
3. Redémarrer Home Assistant
4. Vérifier que l’intégration RTE Tempo se reconnecte avec vos identifiants API existants

Les capteurs Open DPE du fork disparaissent (ou deviennent orphelins).

### 3. Nettoyer les entités orphelines

1. Paramètres → Appareils et services → Entités
2. Filtrer les indisponibles / orphelines liées à `rte_tempo_forecast_*` de l’ancien domaine `rtetempo`
3. Les supprimer

### 4. Aligner les `entity_id` (si besoin)

Si Tempo Prévision a créé par exemple `sensor.rte_tempo_forecast_opendpe_j2_2` :

1. Ouvrir l’entité → Paramètres
2. Renommer l’identifiant d’entité en `sensor.rte_tempo_forecast_opendpe_j2` (idem pour j3…j7, emoji, accuracy)
3. Enregistrer

Les dashboards / automations qui pointaient déjà vers les anciens IDs refonctionnent sans modification.

### 5. Vérifier

- États J+2..J+7 mis à jour (couleur + attributs `date` / `probability` ou `indicator`)
- Capteur accuracy présent **si** `sensor.rte_tempo_couleur_actuelle` (ou l’entité configurée) existe
- Dashboards `examples/` et vos cartes Lovelace

## Options accuracy

Dans les options de Tempo Prévision :

- **Activer la précision** : oui/non
- **Entité couleur réelle** / **lendemain** : laisser vide pour auto-détecter hekmon/rtetempo ; sinon choisir d’autres capteurs

Sans source de couleur réelle, les prévisions J+2..J+7 restent disponibles ; seul le capteur accuracy est omis.

## Rollback

Réinstaller le fork `rjullien/rtetempo` et désactiver Tempo Prévision. Attention : conflit de chemin `custom_components/rtetempo` — ne garder qu’une seule installation `rtetempo` à la fois.
