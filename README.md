# tunisie-simulateur-amen-social

Simulateur du **programme Amen social** (Tunisie), construit sur le moteur de
micro-simulation [OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia),
avec une interface [Shiny for Python](https://shiny.posit.co/py/).

Le programme **Amen social** (loi organique n° 2019-10 du 30 janvier 2019,
décret n° 2020-317 du 19 mai 2020) verse aux ménages pauvres un **transfert
monétaire permanent** (TMP) mensuel : une allocation de base, majorée par enfant
à charge et par enfant lourdement handicapé. Ce simulateur calcule
l'**éligibilité** et le **montant** du TMP pour un ménage donné.

## Architecture

L'application **ne calcule rien elle-même** : elle construit la situation d'un
ménage (composition, revenu, résidence, handicap, décile de ciblage) et demande
les résultats au moteur OpenFisca-Tunisia. OpenFisca reste le moteur unique.

```
Shiny (app/)  ──▶  OpenFisca-Tunisia + réforme corrective  ──▶  moteur de calcul
```

### Réforme corrective (`app/reform.py`)

Dans la version actuelle du modèle (openfisca-tunisia ≤ 0.159), la chaîne du TMP
est **inexécutable** à cause de trois défauts (variable de ciblage non déclarée,
nom de paramètre erroné, formule d'éligibilité absente avant 2022). Une petite
réforme locale les corrige **sans changer le barème**. Détail et correctifs à
remonter en amont : [`docs/notes/desaccords.md`](docs/notes/desaccords.md).

## Lancer en local

Deux modes (variable d'environnement `OPENFISCA_MODE`) :

### Moteur en direct (défaut, recommandé — réforme intégrée)

```bash
uv run shiny run app/app.py --port 8102
```

Puis ouvrir http://localhost:8102.

### API OpenFisca séparée

L'API doit être servie **avec la réforme** (sinon le TMP échoue) :

```bash
cd app && uv run openfisca serve -c openfisca_tunisia -r reform.amen_social_corrections -p 5002
OPENFISCA_MODE=api uv run shiny run app/app.py --port 8102
```

## Entrées / sorties

- **Entrées** : année, nombre d'adultes et d'enfants (grille éditable : âge,
  étudiant, handicap), revenu mensuel du ménage, résidence secondaire, achat
  onéreux récent, décile du score de ciblage.
- **Sorties** : revenu au sens Amen, présence d'un handicap lourd, éligibilité
  (critères primaires), enfants à charge (dont handicapés), éligibilité et
  **montant du transfert monétaire permanent** (mensuel et annuel).

## Barème (mémo)

Allocation de base : 200 DT (2022) → 220 (2023) → 240 (2024) → 260 (2025).
Supplément : **10 DT/enfant à charge** (6-18 ans, 25 ans si étudiant, tout âge
si lourdement handicapé) ; **× 2** pour un enfant handicapé. Éligibilité : revenu
sous un seuil fonction de la taille du ménage (en SMIG), pas de résidence
secondaire, pas d'achat onéreux — ou décile de ciblage ≤ 1.

## Principe de validation

Le **droit fait référence** (loi org. 2019-10, décret 2020-317, arrêtés
conjoints, circulaire n° 12 de 2022). Chaque divergence modèle/texte est
documentée dans [`docs/notes/desaccords.md`](docs/notes/desaccords.md) et
tranchée par le texte. Chaque cas chiffré devient un test.

## Structure

```
app/               Application Shiny + client OpenFisca + réforme corrective
tests/amen_social/ Tests YAML OpenFisca (éligibilité, modèle nu)
tests/             Tests pytest du TMP (via la réforme)
docs/notes/        Désaccords/défauts relevés et backlog
deploy/            Déploiement shinyapps.io (moteur en direct)
sources_locales/   Correspondance cas ↔ source (GITIGNORÉ)
```

## Tests

```bash
uv run openfisca test tests/amen_social/ -c openfisca_tunisia   # éligibilité (modèle nu)
uv run pytest tests/test_transfert_monetaire.py                 # montant du TMP (réforme)
```
