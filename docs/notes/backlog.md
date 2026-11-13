# Backlog — simulateur Amen social

Reports durables (ne doivent vivre ni dans la conversation ni dans une liste de
session). Mis à jour à chaque point d'arrêt.

## État de session (2025-11, relais)

**Livré et déployé** (app en ligne : https://benjello.shinyapps.io/simulateur-amen-social-tunisie/ ; CD GitHub Actions au vert, épinglé `--app-id 18430225`) :

- **v1** : éligibilité + montant du transfert monétaire permanent (TMP), via `app/reform.py` (réforme corrective ; openfisca-tunisia PyPI = 0.164, encore buggé).
- **Axe A** (bouquet) : allocations familiales non contributives (0-5, 6-18 corrigée), allocations catégorielles (gluten, xeroderma), **total des aides** (mensuel + annuel). Entrées cartes AMG1/AMG2/PNAFN + flags santé par enfant. Commit `53ed3e4`.
- **Axe C3** : explication « pourquoi éligible/non » (seuil applicable via variable `amen_social_seuil_revenu`, voie retenue, critères bloquants). Commit `712fd9e`.
- **Axe C2/C4/C5** : export PDF (attestation), graphe (total des aides selon le revenu), comparateur par année. Dépendance matplotlib ajoutée. Commit `afde1e4`.
- **Correctif amont** : PR openfisca-tunisia **#529** (branche `fix/amen-social-tmp`, 0.166), OPEN + mergeable + CI verte. En attente de merge + release PyPI → ensuite retirer la réforme.

- **Anti-non-recours** (axe D3) — **fait** : carte « Comment faire valoir vos droits » (démarche officielle : unité locale de promotion sociale / registre social Amen, pièces, identifiant unique, recours) ou « Que faire ensuite » si non éligible. Sourcé (décret 2020-317, social.gov.tn).
- **Clarté du résultat** — **fait** : le résumé mène avec « Vos aides » (ce que le foyer reçoit) ; le diagnostic technique (revenu, seuil, éligibilités intermédiaires) est replié dans « Détail du calcul ».
- **Estimation instantanée** — **fait** : le résumé se recalcule à chaque réponse (plus besoin de cliquer) ; le bouton ne sert plus qu'au détail lourd (graphique + comparateur).
- **Entonnoir / divulgation progressive** (axe D1) — **fait** : saisie restructurée en parcours par étapes (accordion pleine largeur ① Votre foyer / ② Vos ressources / ③ Logement et biens / ④ Options avancées repliées), questions en langage simple, boutons Oui/Non (plus clairs que des cases), jargon (décile, AMG, PNAFN) replié avec texte rassurant, grille des enfants auto-synchronisée (plus de bouton « générer »). `app/app.py` en `page_fillable`. Commit à suivre.

- **Axe C1 bilingue FR/AR + RTL** — **fait** : sélecteur de langue, bascule **RTL** (message custom JS `setdir`), `ui.update_*` des libellés d'entrées + choix Oui/Non + titres de panneaux sur changement de langue, textes statiques en `output_ui`, et sorties dynamiques (en-tête, bannières, explication par **codes** traduits, D3, tableaux) via `t(cle, lang)`. `app/i18n.py` complet.

**Résidus FR (mineurs, itération ultérieure)** :

- Message `statut_api` (technique, orienté développeur).
- **Graphique** (axes matplotlib) et **PDF** : rendus en français — matplotlib ne gère pas l'arabe RTL sans `arabic-reshaper` + `python-bidi`.
- **Comparateur** : entêtes/colonnes de la grille en français.

**Plans de référence** : `docs/notes/ameliorations-avancees.md` (7 axes A-G) et `docs/notes/plan-a-c-actions.md` (décomposition A/C).

## Prochaines étapes conseillées (ordre)

1. Finir l'**entonnoir** (en cours) + tester + déployer.
2. Câbler **C1 FR/AR** (i18n.py déjà prêt).
3. Vagues suivantes du plan : D3 anti-non-recours, score PMT (axe B), réformes paramétriques (F1).
4. Quand openfisca-tunisia 0.166 est sur PyPI : retirer `app/reform.py`, borne `>=0.166`, basculer tests TMP sur modèle nu.

## À remonter en amont (openfisca-tunisia) — nouveaux (axe A)

- [ ] **`pnafn_eligible` jamais déclarée** : les allocations familiales non
  contributives la lisent, mais `pnafn.py` ne déclare aucune variable →
  `VariableNotFoundError`. Contournée par `app/reform.py` (entrée). Même famille
  de défaut que `amen_social_score_decile`.
- [ ] **Bug `allocation_familiale_non_contributive_6_18`** : tranche d'âge
  `(6 <= age) * (age >= 18)` (seuls les 18 ans et plus) au lieu de `age <= 18`.
  Corrigé dans `app/reform.py` ; à remonter.
- [ ] **Incohérence date formule/paramètre** : `allocation_familiale_non_contributive_0_5`
  a une `formula_2020_06`, mais le paramètre `allocation_familiale` ne débute
  qu'au 2022-04-08 → `ParameterNotFoundError` pour 2020-06 → 2022-03. Soit avancer
  le paramètre, soit retarder la formule. (Le simulateur contourne en renvoyant
  « — » hors période valide.)
- [ ] **`amg_1` / `amg_2` sans formule d'éligibilité** (entrées) : l'éligibilité
  santé AMG n'est pas modélisée. Exposées en saisie dans le simulateur.
- [ ] **Bug latent `_calculate_local` (simulateurs paie/pension)** : le client
  local prenait toujours l'index `[0]` du tableau calculé — faux dès qu'il y a
  plusieurs membres pour une variable Individu. Corrigé ici ; le même patron
  existe dans `../tunisie-simulateur-paie` et `../tunisie-simulateur-pension`
  (sans conséquence tant qu'il n'y a qu'un individu, mais à corriger par sécurité).

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
