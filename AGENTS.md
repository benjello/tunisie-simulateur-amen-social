# AGENTS.md

Instructions et profils d'agents pour ce dépôt, lisibles par n'importe quel
opérateur d'agent (Claude Code, opencode, Cursor, pi…).

## Le projet

Simulateur du **programme Amen social** (Tunisie), construit sur le moteur
[OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia) et une
interface [Shiny for Python](https://shiny.posit.co/py/). Il calcule
l'**éligibilité** et le **montant du transfert monétaire permanent** (TMP) d'un
ménage.

**L'application ne calcule rien elle-même** : elle poste la situation d'un ménage
au moteur OpenFisca-Tunisia et affiche le résultat. OpenFisca est le moteur
unique. Une **réforme corrective** locale (`app/reform.py`) rend la chaîne du TMP
exécutable sans changer le barème (voir `docs/notes/desaccords.md`).

## Règles de travail

- **Le droit fait référence** (loi organique n° 2019-10, décret n° 2020-317,
  arrêtés conjoints Affaires sociales/Finances, circulaire n° 12 de 2022). Les
  simulateurs en ligne sont des points de comparaison, pas la vérité.
- Chaque divergence modèle/texte — ou défaut de code — est **identifiée,
  documentée et tranchée par le texte** dans `docs/notes/desaccords.md`.
- Les **reports durables** vont dans `docs/notes/backlog.md` (jamais seulement
  dans la conversation).
- **Confidentialité des sources** : les noms des simulateurs/cas testés ne
  figurent pas dans le dépôt public ; la correspondance « cas ↔ source » est
  tenue dans `sources_locales/` (gitignoré).
- Tests :
  - éligibilité (modèle nu) : `openfisca test tests/amen_social/ -c openfisca_tunisia` ;
  - montant du TMP (via la réforme) : `pytest tests/test_transfert_monetaire.py`.

## La réforme corrective (`app/reform.py`)

Trois défauts du modèle rendent le TMP inexécutable ; la réforme les corrige
**sans toucher au barème** (détail dans `docs/notes/desaccords.md`) :
1. déclare `amen_social_score_decile` (variable d'entrée, décile de ciblage) ;
2. corrige le paramètre `supplements.enfant_a_charge` dans
   `transfert_monetaire_permanent` ;
3. ajoute une `formula_2020` à `transfert_monetaire_permanent_eligibilite_score`
   (avant la circulaire de 2022, seuls les critères primaires ouvrent le droit).

À remonter en amont (openfisca/openfisca-tunisia) ; voir `docs/notes/backlog.md`.

## Profils d'agents disponibles

**Source unique** : `.pi/agents/*.md`. Les formats `.claude/agents/` et
`.opencode/agent/` sont **générés** par `scripts/deploy_agents.sh` :

```bash
scripts/deploy_agents.sh           # régénère .claude/agents/ et .opencode/agent/
scripts/deploy_agents.sh --global  # + déploie en user
scripts/deploy_agents.sh --check   # vérifie la synchro (CI), sans écrire
```

N'éditez que `.pi/agents/*.md`, puis relancez le script.

- `analyste-openfisca` — analyse du modèle OpenFisca-Tunisia (variables,
  paramètres, enchaînement du calcul). Lecture seule, économe. **Exigence** :
  vérifier les chiffres par le calcul via le venv du projet et sourcer chaque
  paramètre (fichier YAML + date d'effet).
- `juriste-fiscal-tn` — droit tunisien : établir ce que disent les textes (loi
  org. 2019-10, décret 2020-317, arrêtés, circulaires) pour trancher les écarts.
  Lecture seule + recherche web.

## Entités et variables OpenFisca (mémo)

- Prestation au niveau **Ménage** (`menages`, rôles `personne_de_reference`,
  `conjoint`, `enfants`, `ascendants`, `autres`).
- Entrées : `salaire_net_a_payer`/`pension_de_retraite` (membres, revenu Amen),
  `age` (membre), `etudiant` (annuel), `handicap` (0/1/3 ; 3 = lourd),
  `amen_social_pas_de_residence_secondaire`, `amen_social_pas_d_achat_onereux`,
  `amen_social_score_decile` (réforme).
- Sorties : `amen_social_revenu`, `amen_social_eligible`,
  `amen_social_enfants_a_charge`, `amen_social_enfants_handicapes_a_charge`,
  `transfert_monetaire_permanent_eligible`, `transfert_monetaire_permanent`.
- Toutes mensuelles (période `MONTH`), sauf `etudiant` (YEAR) et `handicap`
  (ETERNITY).
