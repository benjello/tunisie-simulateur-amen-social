# Plan d'améliorations avancées — simulateur Amen social

État de départ (v1) : le simulateur calcule l'**éligibilité** et le **montant du
transfert monétaire permanent (TMP)** d'un ménage, via OpenFisca-Tunisia + une
réforme corrective. Entrées : année, composition, revenu, résidence/achat,
**décile de ciblage saisi à la main**. Sorties : éligibilité + montant mensuel.

Ce document liste des améliorations avancées, hiérarchisées, en s'inspirant :
- des **simulateurs frères** (paie, pension) du même groupe ;
- des **autres prestations déjà modélisées** dans openfisca-tunisia mais non exposées ;
- de l'**état de l'art international** des simulateurs d'aide sociale (France
  mes-aides/mesdroitssociaux sur OpenFisca ; UK Turn2us / entitledto / Policy in
  Practice ; approche Banque mondiale / PMT).

Légende : **Impact** (couverture, utilité usager, valeur politique) ·
**Effort** (S/M/L/XL) · **Amont** = nécessite une évolution d'openfisca-tunisia.

---

## A. Faire de l'app un « bouquet Amen », pas seulement le TMP

C'est l'axe le plus utile : à l'image de **mes-aides.org** (un formulaire → ~1000
aides d'un coup), simuler **tous les droits de l'aide sociale** liés à Amen, pas
le seul TMP. Plusieurs prestations sont **déjà dans le modèle** (voir inventaire)
— il « suffit » de les brancher et de les exposer.

| # | Prestation | État modèle | Impact | Effort | Amont |
|---|---|---|---|---|---|
| A1 | **Aides ponctuelles** (Ramadan/Aïd 60 DT, rentrée scolaire 50 DT, rentrée univ., urgence) | **paramètres présents**, pas de variable | Fort | M | oui (créer variables) |
| A2 | **AMG1 / AMG2** (gratuité / tarif réduit des soins) | variables `amg_1`, `amg_2` présentes | Fort | M | partiel |
| A3 | **Allocations familiales non contributives** (0-5, 6-18 ; 30 DT/enfant) | variables présentes (`allocation_familiale_non_contributive_*`) | Fort | S/M | non |
| A4 | **Aides catégorielles santé** (allergie au gluten, xeroderma pigmentosum) | variables présentes | Moyen | S | non |
| A5 | **PNAFN** (ancien programme) + **articulation** avec Amen (cumul/substitution) | paramètres présents | Moyen | M | partiel |
| A6 | **Vue consolidée « total des aides du ménage »** (somme mensuelle + annuelle, par prestation) | — | Fort | S | non |

> Cible : un onglet « Tous mes droits » qui liste chaque prestation (éligible
> oui/non, montant, base légale), façon tableau de synthèse mes-aides.

---

## B. Le chaînon manquant : calculer le score de ciblage (PMT)

Aujourd'hui `amen_social_score_decile` est une **entrée** : l'usager ne connaît
pas son décile, donc la voie « ciblage » est inutilisable en pratique. Or le
cœur du dispositif Amen est le **modèle de notation PMT** (proxy-means test)
prévu par la loi organique 2019-10 et calibré par le CRES / la Banque mondiale.

| # | Chantier | Impact | Effort | Amont |
|---|---|---|---|---|
| B1 | **Implémenter le score PMT** comme variable OpenFisca : index multidimensionnel à partir des caractéristiques du ménage (logement, biens durables, taille/composition, éducation, région, accès eau/électricité…) | Très fort | XL | oui |
| B2 | **Formulaire « caractéristiques du ménage »** alimentant le score (au lieu de saisir le décile) | Très fort | L | — |
| B3 | **Conversion score → décile** (seuils par vague), et affichage du rang | Fort | M | oui |
| B4 | **Transparence** : montrer les variables qui pèsent le plus dans le score (contributions) | Moyen | M | — |

> Sources à exploiter : rapport CRES « Identification des ménages pauvres et
> vulnérables en Tunisie » (variables et régressions du PMT), note Banque
> mondiale P177693, arrêté MAS 2020. C'est un chantier de recherche : prototyper
> via `reform.py`, puis remonter en amont. **Attention** : publier un score de
> ciblage a des enjeux politiques/éthiques (erreurs d'inclusion/exclusion) → à
> encadrer de disclaimers et de la mention « indicatif ».

---

## C. Parité avec les simulateurs frères (paie, pension)

Le simulateur de paie a déjà ces briques ; les porter ici est à faible risque.

| # | Fonction | Vu chez | Impact | Effort |
|---|---|---|---|---|
| C1 | **Bilingue FR/AR + RTL** (module `i18n.py`, bascule de langue) | paie | **Très fort** (public cible arabophone, faible littératie) | M |
| C2 | **Export PDF** d'une attestation de simulation (justificatif à présenter) | paie | Fort | S |
| C3 | **Explication pas-à-pas** : « pourquoi éligible / non » (seuil de revenu applicable, critères bloquants) | — | Fort | M |
| C4 | **Graphique** : montant de l'aide selon le revenu / la composition (visualise le barème et les ruptures) | paie | Moyen | S |
| C5 | **Comparateur** : par année (évolution du barème) et par composition de ménage | paie | Moyen | M |

---

## D. UX « accès aux droits » (leçons France / UK)

Le public d'Amen n'est pas celui d'un simulateur de paie : faible littératie
numérique, enjeu de **non-recours**. Les bonnes pratiques internationales :

| # | Amélioration | Inspiration | Impact | Effort |
|---|---|---|---|---|
| D1 | **Parcours guidé** (questions progressives, ~7 min) au lieu d'un formulaire dense | mes-aides.org | Fort | L |
| D2 | **« Et si… » / better-off** : effet d'un revenu supplémentaire sur l'aide (points de rupture, perte nette éventuelle) | Policy in Practice (UK) | Fort | M |
| D3 | **Anti-non-recours** : « vous semblez éligible → voici comment demander » (bureau des affaires sociales, pièces à fournir, lien) | mes-aides, plan pauvreté FR | **Très fort** | S/M |
| D4 | **Accessibilité** : mobile-first, langage simple, pictogrammes, contraste, compat lecteurs d'écran | Turn2us | Fort | M |
| D5 | **Mode « travailleur social »** : saisie pour un tiers, multi-dossiers, note imprimable | — | Moyen | L |
| D6 | **Recherche de dispositifs connexes** (bourses, transport scolaire, cantine…) | Turn2us « grants search » | Moyen | L |

---

## E. Robustesse, qualité, données

| # | Chantier | Impact | Effort |
|---|---|---|---|
| E1 | **Validation sur cas réels** (communications du ministère, bénéficiaires) → un test par cas ; correspondance cas↔source dans `sources_locales/` | Fort | M |
| E2 | **Affichage des sources légales** (références JORT déjà présentes dans les paramètres : les exposer dans l'UI) | Moyen | S |
| E3 | **Historique multi-années du barème** (déjà partiel : généraliser 2020→courant) | Moyen | S |
| E4 | **PWA / mode dégradé hors-ligne** (zones à faible connectivité) | Moyen | L |
| E5 | **Retrait de la réforme** dès openfisca-tunisia ≥ 0.166 publié (bascule tests TMP sur modèle nu) | Faible | S |
| E6 | **Tests de non-régression** sur toutes les prestations exposées (YAML + pytest) | Fort | M |

---

## F. Analytique et valeur « politique publique »

Au-delà du cas individuel, OpenFisca permet la **micro-simulation** : forte
valeur pour décideurs, bailleurs, société civile.

| # | Chantier | Inspiration | Impact | Effort |
|---|---|---|---|---|
| F1 | **Réformes paramétriques** (curseurs sur montants/seuils) + effet immédiat sur un cas | LexImpact (FR) | Fort | M |
| F2 | **Coût budgétaire agrégé** d'une réforme (ex. +20 DT allocation de base) sur une population type / enquête | OpenFisca-Survey-Manager | Très fort | L |
| F3 | **Ciblage : erreurs d'inclusion/exclusion**, taux de couverture (si microdonnées d'enquête — ENBC, enquête sociale Amen) | Banque mondiale ASPIRE | Fort | XL |
| F4 | **Benchmark international** (allocation/SMIG, part du PIB, couverture) pour mise en perspective | — | Faible | S |

---

## G. Intégration / réutilisation

| # | Chantier | Impact | Effort |
|---|---|---|---|
| G1 | **Exposer l'API / un outil MCP** (cohérent avec le voisin `mcp-socio-fiscal-tunisie`) pour que d'autres apps/assistants calculent Amen | Moyen | M |
| G2 | **Embarquable** (widget iframe) pour sites d'associations / collectivités | Moyen | S |
| G3 | **Lien avec les autres simulateurs** (paie, pension, impôt) : un portail « ma situation socio-fiscale » commun | Fort | L |

---

## Séquencement conseillé

**Vague 1 — parité et accès aux droits (rapide, fort impact usager)**
C1 (FR/AR), C3 (pourquoi éligible), D3 (anti-non-recours), C2 (PDF), A6 (total
des aides), E2/E5.

**Vague 2 — élargir le bouquet (couverture)**
A3 (allocations familiales NC), A1 (aides ponctuelles), A2 (AMG1/2), A4, E1/E6.
Chaque prestation manquante : prototyper via `reform.py`, remonter en amont.

**Vague 3 — le cœur méthodologique (recherche)**
B1→B4 (score PMT) : le vrai différenciateur ; chantier long, à mener avec le
CRES / la littérature Banque mondiale. D1 (parcours guidé) en parallèle.

**Vague 4 — valeur politique publique**
F1 (réformes paramétriques), F2 (coût budgétaire), G1 (MCP/API), G3 (portail).

---

## Dépendances amont (openfisca-tunisia) à ouvrir

- Finaliser/mettre à jour les variables **AMG1/AMG2**, **aides ponctuelles**,
  **allocations familiales non contributives** (certaines marquées TODO dans le
  code), avec tests et références.
- **Score PMT** : nouvelle brique majeure (variables + paramètres du modèle de
  notation). À co-construire avec les détenteurs du barème (MAS, CRES).
- Publier **0.166** (PR #529) pour retirer la réforme locale.

## Sources

- Simulateurs frères : `../tunisie-simulateur-paie` (i18n, PDF, comparateur,
  graphe), `../tunisie-simulateur-pension`.
- Modèle : `openfisca_tunisia/variables/prestations/non_contributives/`,
  `parameters/prestations/non_contributives/`.
- France : mes-aides.org, mesdroitssociaux.gouv.fr, beta.gouv.fr/startups/mes-aides
  (OpenFisca, bouquet d'aides, lutte contre le non-recours).
- UK : Turn2us, entitledto, Policy in Practice « better off calculator »
  (gov.uk/benefits-calculators).
- Ciblage Tunisie : CRES « Identification des ménages pauvres et vulnérables »
  (cres.tn), note Banque mondiale P177693, étude PMT du ministère des Affaires
  sociales (social.gov.tn).
