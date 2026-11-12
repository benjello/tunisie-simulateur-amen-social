"""Client OpenFisca-Tunisia — programme Amen social.

L'app Shiny ne calcule rien elle-même : elle construit la situation d'un ménage
(composition, revenu, résidence, handicap…), puis demande les résultats au
moteur OpenFisca-Tunisia. OpenFisca reste le seul moteur de calcul.

La chaîne du **transfert monétaire permanent** (TMP) est corrigée par une petite
réforme locale (`reform.py`) : deux défauts du modèle la rendent sinon
inexécutable (voir `reform.py` et `docs/notes/desaccords.md`). Le barème n'est
pas modifié.

Deux modes, selon la variable d'environnement OPENFISCA_MODE :
- "local" (défaut ici) : calcule dans le même process via la réforme appliquée au
  CountryTaxBenefitSystem. C'est le mode recommandé (la réforme est intégrée).
- "api" : poste la situation à l'API web sur OPENFISCA_API_URL. L'API doit alors
  être servie **avec la réforme** :
      openfisca serve -c openfisca_tunisia -r reform.amen_social_corrections -p 5002
"""

from __future__ import annotations

import os

import httpx

# URL de l'API OpenFisca Amen social (mode "api"). Surchargée par OPENFISCA_API_URL.
API_URL = os.environ.get("OPENFISCA_API_URL", "http://localhost:5002")

# Mode de calcul : "local" (moteur in-process, réforme intégrée) ou "api" (HTTP).
MODE = os.environ.get("OPENFISCA_MODE", "local").lower()

# TaxBenefitSystem (avec réforme) chargé paresseusement en mode local.
_TBS = None


def _get_tbs():
    global _TBS
    if _TBS is None:
        from openfisca_tunisia import CountryTaxBenefitSystem

        from reform import amen_social_corrections

        _TBS = amen_social_corrections(CountryTaxBenefitSystem())
    return _TBS


def _calculate_local(situation: dict) -> dict:
    """Calcule en direct via SimulationBuilder et renvoie le résultat au format API.

    Toutes les variables à `None` dans la situation sont calculées et remplies,
    pour chaque période demandée ; on imite la structure de réponse de l'API.
    """
    from openfisca_core.simulations import SimulationBuilder

    tbs = _get_tbs()
    builder = SimulationBuilder()
    simulation = builder.build_from_entities(tbs, situation)

    resultat = {k: {} for k in situation}
    for collection, entites in situation.items():
        for ident, variables in entites.items():
            resultat[collection][ident] = {}
            for variable, periodes in variables.items():
                if not isinstance(periodes, dict):
                    resultat[collection][ident][variable] = periodes
                    continue
                resultat[collection][ident][variable] = {}
                for periode, valeur in periodes.items():
                    if valeur is None:
                        valeur = float(simulation.calculate(variable, periode)[0])
                    resultat[collection][ident][variable][periode] = valeur
    return resultat


def _calculate(situation: dict, *, timeout: float = 30.0) -> dict:
    """Route le calcul vers le moteur local ou l'API HTTP selon OPENFISCA_MODE."""
    if MODE == "local":
        return _calculate_local(situation)
    reponse = httpx.post(f"{API_URL}/calculate", json=situation, timeout=timeout)
    reponse.raise_for_status()
    return reponse.json()


# Niveaux de handicap d'un membre (valeur openfisca `handicap` -> libellé UI).
# La formule Amen social retient `handicap >= 3` pour le « handicap lourd » et
# `handicap == 3` pour qualifier un enfant handicapé à charge.
HANDICAP = {0: "Aucun", 1: "Léger", 3: "Lourd"}

# Variables de sortie demandées au moteur (clé -> libellé lisible, unité).
SORTIES = [
    ("amen_social_revenu", "Revenu mensuel du ménage (sens Amen)", "DT"),
    ("amen_social_presence_handicap_lourd", "Présence d'un handicap lourd", "bool"),
    ("amen_social_eligible", "Éligible (critères primaires, décret 2020-317)", "bool"),
    ("amen_social_enfants_a_charge", "Enfants à charge (sens Amen)", "int"),
    ("amen_social_enfants_handicapes_a_charge", "dont enfants handicapés", "int"),
    (
        "transfert_monetaire_permanent_eligible",
        "Éligible au transfert monétaire permanent",
        "bool",
    ),
    ("transfert_monetaire_permanent", "Transfert monétaire permanent (mensuel)", "DT"),
]
SORTIES_CLES = [cle for cle, _, _ in SORTIES]


def construire_situation(
    *,
    annee: int,
    nb_adultes: int,
    enfants: list[dict],
    revenu_mensuel: float,
    residence_secondaire: bool = False,
    achat_onereux: bool = False,
    score_decile: int = 11,
) -> dict:
    """Construit la situation JSON OpenFisca pour un ménage, sur janvier de `annee`.

    - `nb_adultes` : nombre d'adultes (≥ 1). Le premier est personne de référence,
      le second conjoint, les suivants « autres » membres.
    - `enfants` : liste de dicts {age:int, etudiant:bool, handicap:int}.
    - `revenu_mensuel` : revenu total mensuel du ménage (DT), porté sur la
      personne de référence (le modèle somme salaires nets + pensions des membres).
    - `residence_secondaire` / `achat_onereux` : critères primaires d'exclusion.
    - `score_decile` : décile du score de ciblage (1 = plus pauvre ; 11 = hors
      ciblage, défaut). Variable d'entrée ajoutée par la réforme.
    """
    mois = f"{annee}-01"
    an = str(annee)
    nb_adultes = max(int(nb_adultes), 1)

    individus: dict = {}
    roles_reference = []
    roles_conjoint = []
    roles_enfants = []
    roles_autres = []

    for i in range(nb_adultes):
        ident = f"adulte{i}"
        individu = {"age": {mois: 40}}
        if i == 0:
            # Revenu total du ménage porté sur la personne de référence.
            individu["salaire_net_a_payer"] = {mois: float(revenu_mensuel)}
            roles_reference.append(ident)
        elif i == 1:
            roles_conjoint.append(ident)
        else:
            roles_autres.append(ident)
        individus[ident] = individu

    for j, enfant in enumerate(enfants):
        ident = f"enfant{j}"
        individus[ident] = {
            "age": {mois: int(enfant.get("age", 0))},
            "etudiant": {an: bool(enfant.get("etudiant", False))},
            "handicap": {an: int(enfant.get("handicap", 0))},
        }
        roles_enfants.append(ident)

    menage: dict = {
        "personne_de_reference": roles_reference,
        "amen_social_pas_de_residence_secondaire": {mois: not residence_secondaire},
        "amen_social_pas_d_achat_onereux": {mois: not achat_onereux},
        "amen_social_score_decile": {mois: int(score_decile)},
    }
    if roles_conjoint:
        menage["conjoint"] = roles_conjoint
    if roles_enfants:
        menage["enfants"] = roles_enfants
    if roles_autres:
        menage["autres"] = roles_autres
    for cle in SORTIES_CLES:
        menage[cle] = {mois: None}

    return {"individus": individus, "menages": {"m0": menage}}


def calculer(situation: dict, *, annee: int, timeout: float = 30.0) -> dict:
    """Calcule la situation (local ou API) et renvoie les sorties (dict plat)."""
    mois = f"{annee}-01"
    data = _calculate(situation, timeout=timeout)
    menage = data["menages"]["m0"]
    return {cle: menage.get(cle, {}).get(mois) for cle in SORTIES_CLES}


def api_disponible(timeout: float = 3.0) -> bool:
    """Teste la disponibilité du moteur (message clair dans l'UI).

    En mode local, le moteur est toujours disponible (calcul in-process).
    """
    if MODE == "local":
        return True
    try:
        return httpx.get(f"{API_URL}/spec", timeout=timeout).status_code == 200
    except httpx.HTTPError:
        return False
