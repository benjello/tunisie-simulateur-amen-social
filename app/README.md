# Application — programme Amen social (local)

Interface [Shiny for Python](https://shiny.posit.co/py/) pour le simulateur
Amen social. **Tout le calcul est fait par OpenFisca-Tunisia**, via une petite
réforme corrective intégrée (`reform.py`) : l'app construit la situation d'un
ménage et affiche l'éligibilité et le montant du transfert monétaire permanent.

## Lancer en local

Mode « moteur en direct » (défaut, la réforme est intégrée au process) :

```bash
uv run shiny run app/app.py --port 8102
```

Puis ouvrir http://localhost:8102.

Mode API (l'API doit être lancée **avec la réforme**) :

```bash
cd app && uv run openfisca serve -c openfisca_tunisia -r reform.amen_social_corrections -p 5002
OPENFISCA_MODE=api uv run shiny run app/app.py --port 8102
```

## Fichiers

- `reform.py` — réforme corrective minimale (déclare `amen_social_score_decile`,
  corrige le nom de paramètre du TMP, ajoute la formule d'éligibilité pré-2022).
  Ne change pas le barème. À remonter en amont (voir `docs/notes/desaccords.md`).
- `openfisca_client.py` — construction de la situation du ménage (composition,
  revenu, résidence, handicap, décile) et appel du moteur (`/calculate` ou
  calcul in-process via la réforme).
- `app.py` — interface Shiny (grille d'enfants éditable, résumé, détails).

## Périmètre actuel

**Transfert monétaire permanent** (allocation de base + suppléments enfants).
Non couvert : aides ponctuelles, AMG1/AMG2, PNAFN, bilingue FR/AR, export PDF
(voir `docs/notes/backlog.md`).

## Déploiement

Comme les autres simulateurs du groupe : déploiement statique GitHub Pages
impossible (extensions compilées absentes de Pyodide). Moteur en direct sur
shinyapps.io. Voir `deploy/`.
