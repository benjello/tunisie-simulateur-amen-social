# Désaccords et défauts relevés

Le **droit fait référence** (loi organique n° 2019-10 du 30 janvier 2019,
décret n° 2020-317 du 19 mai 2020, arrêtés conjoints Affaires sociales/Finances,
circulaire n° 12 du 12 mai 2022). Chaque écart entre le modèle OpenFisca et le
texte — ou chaque défaut du code — est consigné ici et tranché par le texte.

## Défauts du modèle `openfisca_tunisia` (programme Amen social)

Relevés sur `openfisca-tunisia@0.159` (module
`variables/prestations/non_contributives/amen_social.py`). Les deux rendent le
**transfert monétaire permanent (TMP)** inexécutable ; ils sont corrigés par la
réforme locale `app/reform.py` (sans changer le barème) et **doivent être
remontés en amont**.

### 1. Variable `amen_social_score_decile` jamais déclarée

`transfert_monetaire_permanent_eligibilite_score.formula_2022_06` lit
`menage("amen_social_score_decile", period)`, mais aucune classe ne déclare
cette variable → `VariableNotFoundError` dès qu'on calcule le TMP.

**Correctif réforme** : déclarer `amen_social_score_decile` comme variable
d'entrée (décile 1..10 du score de ciblage, 1 = plus pauvre ; défaut 11 = hors
ciblage). C'est bien une donnée exogène (modèle de ciblage / proxy-means test),
pas une grandeur calculée par le modèle.

### 2. Mauvais nom de paramètre dans le montant du TMP

`transfert_monetaire_permanent.formula_2020` lit
`supplements.amen_social_enfants_a_charge`, alors que le paramètre réel est
`prestations.non_contributives.amen_social.supplements.enfant_a_charge`
→ `ParameterNotFoundError`.

**Correctif réforme** : formule identique, mais pointant `supplements.enfant_a_charge`.
Barème inchangé (10 DT/enfant à charge ; × 2 pour un enfant handicapé).

### 3. Éligibilité TMP absente avant juin 2022

`transfert_monetaire_permanent_eligibilite_score` n'a qu'une `formula_2022_06`.
Pour toute période antérieure (2020-2021, et janvier-mai 2022) la variable
retombe sur sa valeur par défaut (`False`) : le modèle ne rend alors **aucun
ménage éligible au TMP**, alors que le programme verse des transferts depuis
2020 (l'allocation de base est paramétrée dès le 25 mai 2020).

**Correctif réforme** : ajouter une `formula_2020` = `amen_social_eligible` (la
voie du décile/score de ciblage n'apparaît qu'avec la circulaire n° 12 de 2022 ;
avant, seuls les critères primaires du décret 2020-317 ouvrent le droit). La
`formula_2022_06` d'origine est conservée telle quelle.

> **État amont.** Les trois correctifs ont été portés dans la source
> `openfisca-tunisia` (fichier `variables/prestations/non_contributives/amen_social.py`),
> avec un test `tests/formulas/amen_social/transfert_monetaire_permanent.yaml`
> (31 tests Amen social au vert) et une entrée de CHANGELOG (version 0.166). Il
> reste à **ouvrir la PR** et à **publier la release PyPI**. Tant que le paquet
> installé par le simulateur (PyPI, actuellement 0.164) ne contient pas le
> correctif, le simulateur garde `app/reform.py`. Dès que 0.166+ est installé,
> la réforme devient inutile et peut être retirée.
>
> ⚠️ Les éditions amont ont été faites dans l'arbre de travail de
> `../openfisca-tunisia`, qui était sur la branche `fix/pension-script-ast-lecture-seule`
> (travail pension sans rapport). **À déplacer sur une branche dédiée** (p. ex.
> `fix/amen-social-tmp`) avant commit/PR, pour ne pas mélanger les deux sujets.

## Barème de référence (pour mémoire)

- **Allocation de base (mensuelle)** : 180 DT (2020) → 200 (2022) → 220 (2023)
  → 240 (2024) → 260 (2025) → 280 (2026). Arrêté du 19 mai 2020, art. 2, puis
  lois de finances successives.
- **Supplément par enfant à charge** : 10 DT. Enfant à charge = 6 à 18 ans
  (25 ans si étudiant), ou tout âge si lourdement handicapé.
- **Majoration enfant handicapé** : × 2 (soit 20 DT).
- **Seuils d'éligibilité (revenu mensuel du ménage, en SMIG 48 h)** :
  1 pers. 0,667 ; 2 pers. 1 ; 3-4 pers. 1,5 ; ≥ 5 pers. 2. Majorés en présence
  d'un handicap lourd : 1,167 / 1,5 / 2 / 2,5.
- **Décile de ciblage** ouvrant droit au TMP : 1 (circulaire n° 12 du 12 mai
  2022).
