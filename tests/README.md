# Tests

Deux niveaux, selon qu'ils dépendent ou non de la réforme corrective.

## Éligibilité — modèle nu (`tests/amen_social/*.yaml`)

Tests YAML OpenFisca sur les variables d'éligibilité, exécutables sans réforme :

```bash
uv run openfisca test tests/amen_social/ -c openfisca_tunisia
```

Couvrent `amen_social_revenu`, `amen_social_eligible`,
`amen_social_enfants_a_charge`, `amen_social_enfants_handicapes_a_charge`,
`amen_social_presence_handicap_lourd`.

## Montant du transfert monétaire permanent (`tests/test_transfert_monetaire.py`)

La chaîne du TMP est inexécutable sur le modèle nu (trois défauts corrigés par
`app/reform.py`). Ces tests passent donc par le client en mode « moteur en
direct » (`OPENFISCA_MODE=local`), qui applique la réforme :

```bash
uv run pytest tests/test_transfert_monetaire.py
```

Vérifient le barème (allocation de base par année, suppléments enfants et
handicap), les voies d'éligibilité (critères primaires et décile) et les
exclusions (revenu, résidence secondaire).

## Convention

Le **droit fait référence**. Chaque cas chiffré tiré d'une source externe
devient un test ; la correspondance « cas ↔ source » est tenue dans
`sources_locales/` (gitignoré). Voir `docs/notes/desaccords.md`.
