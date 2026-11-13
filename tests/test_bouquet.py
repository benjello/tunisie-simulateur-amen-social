"""Tests du « bouquet » de prestations (axe A) via la réforme (mode local).

Couvre les prestations non contributives exposées en plus du TMP : allocations
familiales non contributives (0-5 et 6-18, cette dernière corrigée par la
réforme), allocation pour allergie au gluten, et le total consolidé.

    uv run pytest tests/test_bouquet.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("OPENFISCA_MODE", "local")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from openfisca_client import calculer, construire_situation  # noqa: E402


def _res(**kwargs):
    annee = kwargs.pop("annee", 2025)
    return calculer(construire_situation(annee=annee, **kwargs), annee=annee)


def test_allocation_familiale_nc_0_5_liee_a_amen():
    # Ménage éligible Amen, 1 enfant de 3 ans -> alloc. familiale NC 0-5 = 30.
    res = _res(nb_adultes=1, enfants=[{"age": 3}], revenu_mensuel=100)
    assert bool(res["amen_social_eligible"]) is True
    assert abs(res["allocation_familiale_non_contributive"] - 30.0) < 0.01


def test_allocation_familiale_nc_6_18_corrige():
    # Correctif réforme : un enfant de 10 ans (6-18) doit compter.
    # Dépend d'une carte AMG (l'éligibilité 6-18 ne passe pas par Amen).
    res = _res(nb_adultes=1, enfants=[{"age": 10}], revenu_mensuel=100, amg1=True)
    assert abs(res["allocation_familiale_non_contributive"] - 30.0) < 0.01


def test_gluten_necessite_carte_amg():
    enfant_gluten = {"age": 10, "allergie_gluten": True}
    # Sans carte AMG : pas d'allocation gluten.
    sans = _res(nb_adultes=1, enfants=[enfant_gluten], revenu_mensuel=100)
    assert sans["allocation_allergie_gluten"] == 0.0
    # Avec carte AMG2 : 30 DT (loi de finances 2025).
    avec = _res(
        nb_adultes=1, enfants=[enfant_gluten], revenu_mensuel=100, amg2=True
    )
    assert abs(avec["allocation_allergie_gluten"] - 30.0) < 0.01


def test_total_aides_consolide():
    # 2 adultes + 3 enfants (3, 10, 16) ; éligible Amen ; carte AMG2 ; 1 gluten.
    # TMP 2025 = 260 + 2 enfants à charge x 10 = 280.
    # Alloc. fam. NC = 30 (0-5 : 3 ans) + 60 (6-18 : 10 et 16 ans) = 90.
    # Gluten = 30. Total = 400.
    res = _res(
        nb_adultes=2,
        enfants=[{"age": 3}, {"age": 10, "allergie_gluten": True}, {"age": 16}],
        revenu_mensuel=150,
        amg2=True,
    )
    assert abs(res["transfert_monetaire_permanent"] - 280.0) < 0.01
    assert abs(res["allocation_familiale_non_contributive"] - 90.0) < 0.01
    assert abs(res["allocation_allergie_gluten"] - 30.0) < 0.01
    assert abs(res["total_aides_mensuel"] - 400.0) < 0.01


def test_total_nul_si_non_eligible():
    # Ménage à revenu élevé, aucune carte -> aucune aide.
    res = _res(nb_adultes=2, enfants=[{"age": 10}], revenu_mensuel=5000)
    assert res["total_aides_mensuel"] == 0.0
