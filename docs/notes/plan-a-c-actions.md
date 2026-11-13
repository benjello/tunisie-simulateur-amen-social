# Plan détaillé en actions — Axes A (bouquet) et C (parité)

Décomposition opérationnelle de `ameliorations-avancees.md`, axes **A** et **C**,
**ancrée sur ce que le modèle sait réellement calculer** (instruction faite le
2025-11). À exécuter dans l'ordre des phases.

## Ce que le modèle permet aujourd'hui (constats d'instruction)

Prestations non contributives et leur **calculabilité** :

| Prestation | Entité | Formule ? | Dépend de | Verdict simulateur |
|---|---|---|---|---|
| `transfert_monetaire_permanent` (TMP) | Ménage | oui (via réforme) | éligibilité Amen / décile | **exposé (v1)** |
| `allocation_familiale_non_contributive_0_5` | Ménage | oui (2020-06) | `amen_social_eligible` **+** `amg_1/amg_2/pnafn_eligible` | **calculable** (lié à Amen) |
| `allocation_familiale_non_contributive_6_18` | Ménage | oui (2022-07) **BUGGÉE** | `pnafn_eligible + amg_1/amg_2` | calculable **après fix** |
| `allocation_allergie_gluten` | Individu | oui (2025-01) | `menage_amen_social_pauvre_ou_revenu_limite` (=`amg_1+amg_2`) + flag gluten | calculable si carte AMG saisie |
| `allocation_xeroderma_pigmentosum` | Individu | oui (2026-01) | flag maladie (+ couverture sociale) | calculable (niche, récent) |
| `amg_1`, `amg_2` | Ménage | **aucune** (entrées) | — | **saisie usager** (pas calculé) |
| `pnafn_eligible` | Ménage | **aucune** | — | **saisie usager** |

**Conséquences de conception :**
1. `amg_1`, `amg_2`, `pnafn` ne sont pas calculés par le modèle → on les expose en
   **cases à cocher** (« titulaire carte AMG1 / AMG2 », « bénéficiaire PNAFN »).
   Beaucoup d'aides du bouquet en dépendent.
2. **Bug amont repéré** dans `allocation_familiale_non_contributive_6_18` :
   `enfant_a_charge_6_18 = (6 <= age) * (age >= 18)` ne compte que les 18 ans et
   plus (devrait être `age <= 18`). À corriger via `reform.py` **et** à remonter
   en amont (PR séparée).
3. La **montée en charge par date** diffère selon la prestation (0-5 : 2020-06 ;
   6-18 : 2022-07 ; gluten : 2025 ; xeroderma : 2026). L'UI doit rester cohérente
   avec l'année choisie (afficher « — » quand non en vigueur).

---

## AXE A — « bouquet Amen » (plusieurs prestations + total)

### A-0. Étendre la réforme (`app/reform.py`)
- [ ] Corriger `allocation_familiale_non_contributive_6_18` (`age <= 18`).
- [ ] Vérifier par le calcul (venv du simulateur) les montants attendus.

### A-1. Nouvelles entrées de ménage (client `construire_situation`)
- [ ] `amg_1`, `amg_2` (bool, Ménage, MONTH) ← cases à cocher.
- [ ] `pnafn_eligible` (bool, Ménage, MONTH) ← case à cocher *(input ; absence de
      formule à documenter)*.
- [ ] Par enfant/membre : flags `allergie_gluten`, `xeroderma_pigmentosum`
      (Individu, MONTH) + `couverture_sociale_legale` ← colonnes de la grille.

### A-2. Nouvelles sorties (client `SORTIES` + calcul)
- [ ] `allocation_familiale_non_contributive` (somme 0-5 + 6-18), et le détail
      `_0_5` / `_6_18`.
- [ ] `allocation_allergie_gluten`, `allocation_xeroderma_pigmentosum` (Individu
      → sommer sur le ménage pour l'affichage consolidé).
- [ ] **A6 — vue consolidée** : `total_aides_mensuel` = TMP + alloc. familiales
      NC + allocations catégorielles ; + équivalent annuel (×12).

### A-3. UI (onglet « Tous mes droits »)
- [ ] Tableau : une ligne par prestation (libellé, éligible oui/non, montant
      mensuel, base légale), + ligne **Total**.
- [ ] « — » quand la prestation n'est pas en vigueur l'année choisie.

### A-4. Hors périmètre immédiat (à documenter en backlog)
- AMG1/AMG2 **calculés** (éligibilité santé) : pas de formule amont → reste en
  saisie. Chantier amont.
- Aides ponctuelles (Ramadan/Aïd/rentrée/urgence) : **paramètres** présents mais
  **aucune variable** → nécessite création amont (A1 du plan). Reporté.

---

## AXE C — parité avec paie/pension

### C1. Bilingue FR/AR + RTL
- [ ] Créer `app/i18n.py` : dict plat `clé -> {"fr":…, "ar":…}` + `t(cle, lang)`
      (copier le patron de `../tunisie-simulateur-paie/app/i18n.py`).
- [ ] Traduire tous les libellés (entrées, sorties, prestations, messages,
      explications).
- [ ] Sélecteur de langue + bascule **RTL** (`document.dir='rtl'` en arabe),
      mise à jour des `label=` via `ui.update_*`.

### C3. Explication pas-à-pas de l'éligibilité *(fait avant C2/C4/C5 : valeur forte)*
- [ ] Fonction (client) qui, à partir de la situation + résultats, renvoie les
      **raisons** : seuil de revenu applicable (taille du ménage, handicap
      lourd), revenu du ménage vs seuil, critères bloquants (résidence secondaire,
      achat onéreux), voie d'éligibilité retenue (critères primaires vs décile).
- [ ] Encart « Pourquoi ce résultat » (éligible : par quelle voie ; non éligible :
      quel(s) critère(s) manquant(s), et de combien le revenu dépasse le seuil).

### C2. Export PDF
- [ ] `download_button` → PDF d'attestation (situation + tableau des aides +
      explication). Reportlab ou impression HTML→PDF ; ajouter la dépendance au
      `requirements.txt` de déploiement.

### C4. Graphique
- [ ] Courbe « montant total des aides selon le revenu du ménage » (0 → ~2×seuil)
      pour la composition saisie : visualise le seuil et la rupture d'éligibilité.
- [ ] `matplotlib` (ré-ajouter la dépendance retirée en phase déploiement).

### C5. Comparateur
- [ ] Onglet comparant le **total des aides** par **année** (2020→courant) et/ou
      par **composition** (ex. +1 enfant), à situation financière constante.

---

## Phalange de tests (axe E, en continu)

- [ ] YAML (modèle nu) : allocation familiale NC 0-5 (éligible Amen), carte AMG.
- [ ] pytest (réforme) : bug 6-18 corrigé, total des aides, gluten/xeroderma.
- [ ] Vérifier **chaque montant par le calcul** avant de l'afficher (discipline
      analyste : un chiffre vérifié vaut mieux qu'un chiffre supposé).

## Séquencement d'exécution

1. **A-0 + A-1 + A-2** (moteur : réforme étendue + client bouquet + total) → tests.
2. **A-3** (onglet « Tous mes droits »).
3. **C3** (explication) — forte valeur, peu coûteux.
4. **C1** (FR/AR) — gros volume de traduction mais mécanique.
5. **C2 / C4 / C5** (PDF, graphe, comparateur).
6. Tests complets + déploiement (push.sh / CD) + maj `requirements.txt`.

## Remontées amont générées (à verser au backlog openfisca-tunisia)

- Bug `allocation_familiale_non_contributive_6_18` (`age >= 18` → `age <= 18`).
- Absence de formule pour `amg_1`, `amg_2`, `pnafn_eligible` (éligibilité santé /
  PNAFN non modélisée).
- Aides ponctuelles : paramètres sans variables.
