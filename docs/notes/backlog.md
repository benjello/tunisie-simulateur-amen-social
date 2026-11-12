# Backlog — simulateur Amen social

Reports durables (ne doivent vivre ni dans la conversation ni dans une liste de
session). Mis à jour à chaque point d'arrêt.

## À remonter en amont (openfisca-tunisia)

- [x] **Correctif Amen social** appliqué dans la source `../openfisca-tunisia`
  (`variables/prestations/non_contributives/amen_social.py`) : déclaration de
  `amen_social_score_decile`, correction du paramètre `supplements.enfant_a_charge`,
  `formula_2020` ajoutée à `transfert_monetaire_permanent_eligibilite_score`.
  Test `tests/formulas/amen_social/transfert_monetaire_permanent.yaml` (5 cas) +
  entrée CHANGELOG (0.166). 31 tests Amen social au vert, 334 tests `formulas`
  inchangés.
- [ ] **Commit + PR + release PyPI** : déplacer ces éditions (faites dans l'arbre
  de travail, branche pension) sur une branche dédiée `fix/amen-social-tmp`,
  ouvrir la PR, publier 0.166.
- [ ] Quand 0.166+ est sur PyPI : **retirer `app/reform.py`** du simulateur
  (mettre à jour `openfisca_client.py`, `deploy/`, la borne `openfisca-tunisia>=0.166`)
  et basculer les tests TMP du mode réforme vers le modèle nu / l'API.
- [ ] `transfert_monetaire_permanent_eligibilite_supplementaire` est déclarée
  sans formule (toujours `False`) : clarifier son rôle (critères supplémentaires
  d'éligibilité) et la documenter ou l'implémenter.

## Périmètre non couvert (v1)

- [ ] **Aides ponctuelles** (appui financier occasionnel, loi org. art. 12) :
  fêtes religieuses (Ramadan, Aïd al-Fitr, Aïd al-Adha : 60 DT), rentrée
  scolaire (50 DT) / universitaire, aides d'urgence. Les paramètres existent
  dans le modèle mais ne sont pas exposés par le simulateur.
- [ ] **AMG1 / AMG2** (assurance maladie gratuite / à tarif réduit) et **PNAFN**
  (ancien programme, allocation forfaitaire) : non modélisés dans le simulateur.
- [ ] **Allocations familiales Amen** (30 DT, 0-18 ans) mentionnées en TODO du
  modèle : non implémentées.
- [ ] Le **score de ciblage** est saisi en entrée (décile). Pas de reproduction
  du proxy-means test (hors périmètre).

## Interface / déploiement

- [ ] Interface **bilingue FR/AR** (comme le simulateur de paie) : non faite.
- [ ] **Export PDF** d'une attestation de simulation : non fait.
- [ ] Déploiement shinyapps.io à tester (scaffolding présent dans `deploy/`).
- [ ] En **mode API**, l'API doit être servie avec la réforme
  (`-r reform.amen_social_corrections`) ; vérifier que `openfisca serve` résout
  bien le module `reform` (PYTHONPATH sur `app/`).

## Validation

- [ ] Confronter les montants à des **cas réels** (bénéficiaires, communication
  du ministère des Affaires sociales) et verser chaque cas chiffré en test.
  La correspondance « cas ↔ source » va dans `sources_locales/` (gitignoré).
