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
        # L'index d'une instance dans le tableau calculé suit l'ordre d'insertion
        # des entités (SimulationBuilder). Indispensable dès qu'il y a plusieurs
        # membres : une variable Individu renvoie un tableau, et la valeur du
        # k-ième membre est à l'index k (et non toujours 0).
        for index, (ident, variables) in enumerate(entites.items()):
            resultat[collection][ident] = {}
            for variable, periodes in variables.items():
                if not isinstance(periodes, dict):
                    resultat[collection][ident][variable] = periodes
                    continue
                resultat[collection][ident][variable] = {}
                for periode, valeur in periodes.items():
                    if valeur is None:
                        # Résilience : une prestation dont la formule ou le
                        # paramètre n'existe pas à cette période (ex. allocation
                        # familiale NC avant 2022-04, gluten avant 2025) renvoie
                        # None plutôt que de faire échouer tout le calcul.
                        try:
                            valeur = float(
                                simulation.calculate(variable, periode)[index]
                            )
                        except Exception:
                            valeur = None
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

# --- Prestations du « bouquet » (aides avec montant) ---
# Chaque aide : (clé, libellé, entité "menage"/"individu", année d'entrée en vigueur).
# L'année sert à afficher « — » quand la prestation n'existe pas encore.
AIDES = [
    ("transfert_monetaire_permanent", "Transfert monétaire permanent", "menage", 2020),
    (
        "allocation_familiale_non_contributive",
        "Allocation familiale (non contributive)",
        "menage",
        2020,
    ),
    ("allocation_allergie_gluten", "Allocation allergie au gluten", "individu", 2025),
    (
        "allocation_xeroderma_pigmentosum",
        "Allocation xeroderma pigmentosum",
        "individu",
        2026,
    ),
]

# Variables de diagnostic (éligibilité, revenu…) — toutes au niveau Ménage.
DIAGNOSTIC = [
    ("amen_social_revenu", "Revenu mensuel du ménage (sens Amen)", "DT"),
    ("amen_social_seuil_revenu", "Seuil de revenu applicable (critères primaires)", "DT"),
    ("amen_social_presence_handicap_lourd", "Présence d'un handicap lourd", "bool"),
    ("amen_social_eligible", "Éligible Amen (critères primaires, décret 2020-317)", "bool"),
    ("amen_social_enfants_a_charge", "Enfants à charge (sens Amen)", "int"),
    ("amen_social_enfants_handicapes_a_charge", "dont enfants handicapés", "int"),
    (
        "transfert_monetaire_permanent_eligible",
        "Éligible au transfert monétaire permanent",
        "bool",
    ),
]

# Listes de requête au moteur (par entité).
VARIABLES_MENAGE = [c for c, _, e, _ in AIDES if e == "menage"] + [
    c for c, _, _ in DIAGNOSTIC
]
VARIABLES_INDIVIDU = [c for c, _, e, _ in AIDES if e == "individu"]

# Liste d'affichage (diagnostic + aides + total), au format (clé, libellé, unité).
SORTIES = (
    DIAGNOSTIC
    + [(c, lib, "DT") for c, lib, _, _ in AIDES]
    + [("total_aides_mensuel", "TOTAL des aides (mensuel)", "DT")]
)


def construire_situation(
    *,
    annee: int,
    nb_adultes: int,
    enfants: list[dict],
    revenu_mensuel: float,
    residence_secondaire: bool = False,
    achat_onereux: bool = False,
    score_decile: int = 11,
    amg1: bool = False,
    amg2: bool = False,
    pnafn: bool = False,
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
        individu = {
            "age": {mois: int(enfant.get("age", 0))},
            "etudiant": {an: bool(enfant.get("etudiant", False))},
            "handicap": {an: int(enfant.get("handicap", 0))},
        }
        if enfant.get("allergie_gluten"):
            individu["allergie_gluten"] = {mois: True}
        if enfant.get("xeroderma"):
            individu["xeroderma_pigmentosum"] = {mois: True}
        individus[ident] = individu
        roles_enfants.append(ident)

    # Les aides individuelles (gluten, xeroderma) sont demandées sur chaque membre
    # pour pouvoir les sommer sur le ménage à l'affichage.
    for individu in individus.values():
        for cle in VARIABLES_INDIVIDU:
            individu[cle] = {mois: None}

    menage: dict = {
        "personne_de_reference": roles_reference,
        "amen_social_pas_de_residence_secondaire": {mois: not residence_secondaire},
        "amen_social_pas_d_achat_onereux": {mois: not achat_onereux},
        "amen_social_score_decile": {mois: int(score_decile)},
        "amg_1": {mois: bool(amg1)},
        "amg_2": {mois: bool(amg2)},
        "pnafn_eligible": {mois: bool(pnafn)},
    }
    if roles_conjoint:
        menage["conjoint"] = roles_conjoint
    if roles_enfants:
        menage["enfants"] = roles_enfants
    if roles_autres:
        menage["autres"] = roles_autres
    for cle in VARIABLES_MENAGE:
        menage[cle] = {mois: None}

    return {"individus": individus, "menages": {"m0": menage}}


def calculer(situation: dict, *, annee: int, timeout: float = 30.0) -> dict:
    """Calcule la situation (local ou API) et renvoie les sorties (dict plat).

    Les aides de niveau Individu (gluten, xeroderma) sont **sommées sur le
    ménage**. Une clé `total_aides_mensuel` agrège toutes les prestations.
    """
    mois = f"{annee}-01"
    data = _calculate(situation, timeout=timeout)
    menage = data["menages"]["m0"]
    res = {cle: menage.get(cle, {}).get(mois) for cle in VARIABLES_MENAGE}
    # Somme des aides individuelles sur tous les membres du ménage.
    for cle in VARIABLES_INDIVIDU:
        total = 0.0
        for individu in data["individus"].values():
            valeur = individu.get(cle, {}).get(mois)
            if valeur is not None:
                total += float(valeur)
        res[cle] = total
    # Total des aides du ménage (toutes prestations du bouquet).
    res["total_aides_mensuel"] = sum(
        float(res.get(cle) or 0.0) for cle, _, _, _ in AIDES
    )
    return res


def expliquer_eligibilite(
    resultats: dict,
    *,
    residence_secondaire: bool,
    achat_onereux: bool,
    score_decile: int,
    decile_seuil: int = 1,
) -> dict:
    """Construit l'explication « pourquoi ce résultat » (axe C3), **traduisible**.

    Renvoie `{"eligible": bool, "voie_code": str|None, "raisons": [dict]}`. Chaque
    raison est un dict `{"code": str, ...params numériques}` : la mise en forme et
    la traduction sont faites par l'appelant (via `i18n.t`). Codes de voie :
    `v_primaire`, `v_decile`.
    """
    revenu = resultats.get("amen_social_revenu")
    seuil = resultats.get("amen_social_seuil_revenu")
    eligible_primaire = bool(resultats.get("amen_social_eligible"))
    tmp_eligible = bool(resultats.get("transfert_monetaire_permanent_eligible"))
    par_decile = int(score_decile) <= int(decile_seuil)

    raisons: list[dict] = []
    voie_code = None

    if tmp_eligible:
        if eligible_primaire:
            voie_code = "v_primaire"
            if revenu is not None and seuil is not None:
                raisons.append(
                    {"code": "r_revenu_sous_seuil", "revenu": revenu, "seuil": seuil}
                )
            raisons.append({"code": "r_pas_exclusion"})
        elif par_decile:
            voie_code = "v_decile"
            raisons.append(
                {"code": "r_decile", "decile": int(score_decile), "seuil": int(decile_seuil)}
            )
    else:
        if residence_secondaire:
            raisons.append({"code": "r_res_secondaire"})
        if achat_onereux:
            raisons.append({"code": "r_achat"})
        if revenu is not None and seuil is not None and revenu > seuil:
            raisons.append(
                {
                    "code": "r_revenu_sur_seuil",
                    "revenu": revenu,
                    "seuil": seuil,
                    "ecart": revenu - seuil,
                }
            )
        if not par_decile:
            raisons.append(
                {"code": "r_non_decile", "decile": int(score_decile), "seuil": int(decile_seuil)}
            )
        if not raisons:
            raisons.append({"code": "r_aucun"})

    return {"eligible": tmp_eligible, "voie_code": voie_code, "raisons": raisons}


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
