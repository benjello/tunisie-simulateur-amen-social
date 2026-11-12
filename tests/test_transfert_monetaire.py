"""Tests du transfert monétaire permanent (TMP) via la réforme corrective.

Le montant du TMP n'est pas testable sur le modèle nu (deux défauts corrigés par
`app/reform.py`). On passe donc par le client en mode « moteur en direct »
(OPENFISCA_MODE=local), qui applique la réforme.

Barème 2024 : allocation de base 240 DT + 10 DT/enfant à charge
+ 20 DT/enfant handicapé à charge (10 × majoration 2).

    uv run pytest tests/test_transfert_monetaire.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("OPENFISCA_MODE", "local")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from openfisca_client import calculer, construire_situation  # noqa: E402


def _tmp(**kwargs):
    annee = kwargs.pop("annee", 2024)
    situation = construire_situation(annee=annee, **kwargs)
    return calculer(situation, annee=annee)


def test_eligible_primaire_avec_enfants():
    # 2 adultes + 2 enfants (dont 1 lourd), revenu 150 DT -> éligible.
    # 240 + 2 x 10 + 1 x 20 = 280.
    res = _tmp(
        nb_adultes=2,
        enfants=[{"age": 8}, {"age": 12, "handicap": 3}],
        revenu_mensuel=150,
    )
    assert bool(res["amen_social_eligible"]) is True
    assert res["amen_social_enfants_a_charge"] == 2
    assert res["amen_social_enfants_handicapes_a_charge"] == 1
    assert abs(res["transfert_monetaire_permanent"] - 280.0) < 0.01


def test_revenu_eleve_non_eligible():
    res = _tmp(nb_adultes=2, enfants=[{"age": 8}], revenu_mensuel=2000)
    assert bool(res["amen_social_eligible"]) is False
    assert res["transfert_monetaire_permanent"] == 0.0


def test_eligibilite_par_decile():
    # Revenu élevé mais décile de ciblage = 1 -> éligible, TMP = base seule (240).
    res = _tmp(nb_adultes=1, enfants=[], revenu_mensuel=5000, score_decile=1)
    assert bool(res["amen_social_eligible"]) is False
    assert bool(res["transfert_monetaire_permanent_eligible"]) is True
    assert abs(res["transfert_monetaire_permanent"] - 240.0) < 0.01


def test_residence_secondaire_exclut():
    res = _tmp(
        nb_adultes=1, enfants=[], revenu_mensuel=150, residence_secondaire=True
    )
    assert bool(res["amen_social_eligible"]) is False
    assert res["transfert_monetaire_permanent"] == 0.0


def test_allocation_base_evolue_par_annee():
    # Allocation de base : 200 (2022), 220 (2023), 240 (2024), 260 (2025).
    for annee, base in [(2022, 200), (2023, 220), (2024, 240), (2025, 260)]:
        res = _tmp(annee=annee, nb_adultes=1, enfants=[], revenu_mensuel=50)
        assert abs(res["transfert_monetaire_permanent"] - base) < 0.01, annee
