"""Réforme corrective minimale du module Amen social d'OpenFisca-Tunisia.

Le simulateur **ne calcule rien lui-même** : tout passe par le moteur
OpenFisca-Tunisia. Mais, dans la version actuelle du modèle
(openfisca-tunisia ≤ 0.159), la chaîne du **transfert monétaire permanent**
(TMP) est inexécutable à cause de deux défauts :

1. La variable `amen_social_score_decile`, utilisée par
   `transfert_monetaire_permanent_eligibilite_score`, n'est **déclarée nulle
   part** → `VariableNotFoundError`.
2. La formule de `transfert_monetaire_permanent` lit le paramètre
   `supplements.amen_social_enfants_a_charge`, alors que le paramètre réel
   s'appelle `supplements.enfant_a_charge` → `ParameterNotFoundError`.

Cette réforme corrige ces points **sans changer le barème** et expose, pour le
« bouquet » de prestations (axe A), quelques variables d'entrée manquantes :

- déclare `amen_social_score_decile` (décile du score de ciblage ; défaut 11) ;
- redéfinit la formule du TMP avec le bon nom de paramètre ;
- ajoute une `formula_2020` à l'éligibilité du TMP (critères primaires avant 2022) ;
- déclare `pnafn_eligible` (entrée), lue par les allocations familiales non
  contributives mais non déclarée dans le modèle (`pnafn.py` est vide) ;
- corrige `allocation_familiale_non_contributive_6_18`, dont la tranche d'âge
  était `(6 <= age) * (age >= 18)` (seuls les 18 ans et plus) au lieu de 6-18 ans.

Le calcul reste celui du modèle. Tous les correctifs doivent être remontés en
amont (voir `docs/notes/desaccords.md` et `docs/notes/backlog.md`).
"""

from __future__ import annotations

import numpy as np
from openfisca_core.periods import MONTH
from openfisca_core.reforms import Reform
from openfisca_core.variables import Variable

from openfisca_tunisia.entities import Menage


class amen_social_score_decile(Variable):
    value_type = int
    entity = Menage
    default_value = 11  # hors ciblage par défaut (déciles 1..10 ; 11 = non classé)
    label = "Décile du score de ciblage Amen social (1 = ménage le plus pauvre)"
    definition_period = MONTH
    # Variable d'entrée : score issu du modèle de ciblage (proxy-means test).
    # Non modélisée dans openfisca-tunisia ; fournie par l'utilisateur.


class amen_social_seuil_revenu(Variable):
    value_type = float
    entity = Menage
    label = "Seuil de revenu mensuel d'éligibilité Amen (critères primaires)"
    definition_period = MONTH

    def formula_2020(menage, period, parameters):
        # Reproduit le seuil utilisé par `amen_social_eligible` (décret 2020-317,
        # art. 5) : multiple du SMIG 48 h selon la taille du ménage, majoré en
        # présence d'un handicap lourd. Exposé pour l'explication d'éligibilité.
        smig_mensuel = parameters(period.start).marche_travail.smig_48h_mensuel
        seuil = parameters(period).prestations.non_contributives.amen_social.eligibilite
        taille = menage.nb_persons()
        handicap = menage("amen_social_presence_handicap_lourd", period)
        conditions = [
            taille == 1,
            taille == 2,
            (taille == 3) + (taille == 4),
            taille >= 5,
        ]
        sans_handicap = [
            smig_mensuel * seuil.un_membre,
            smig_mensuel * seuil.deux_membres,
            smig_mensuel * seuil.trois_quatre_membres,
            smig_mensuel * seuil.plus_de_cinq_membres,
        ]
        avec_handicap = [
            smig_mensuel * seuil.handicap_lourd.un_membre,
            smig_mensuel * seuil.handicap_lourd.deux_membres,
            smig_mensuel * seuil.handicap_lourd.trois_quatre_membres,
            smig_mensuel * seuil.handicap_lourd.plus_de_cinq_membres,
        ]
        return np.where(
            handicap,
            np.select(conditions, avec_handicap, default=0.0),
            np.select(conditions, sans_handicap, default=0.0),
        )


class pnafn_eligible(Variable):
    value_type = bool
    entity = Menage
    default_value = False
    label = "Bénéficiaire du PNAFN (programme national d'aide aux familles nécessiteuses)"
    definition_period = MONTH
    # Variable d'entrée : l'éligibilité PNAFN n'est pas modélisée dans
    # openfisca-tunisia (pnafn.py ne déclare aucune variable), alors que les
    # allocations familiales non contributives la lisent. On la déclare en
    # entrée (titulaire d'une carte PNAFN, oui/non). À remonter en amont.


class allocation_familiale_non_contributive_6_18(Variable):
    value_type = float
    entity = Menage
    label = "Allocation familiale (6-18 ans) pour les ménages non affiliés à un régime de sécurité sociale"
    definition_period = MONTH

    def formula_2022_07(menage, period, parameters):
        # Correctif : le modèle amont compte `(6 <= age) * (age >= 18)`, qui ne
        # retient que les 18 ans et plus. La tranche visée est 6 à 18 ans inclus.
        age = menage.members("age", period)
        eligible = menage(
            "eligible_allocation_familiale_non_contributive_6_18", period
        )
        enfant_a_charge_6_18 = (6 <= age) * (age <= 18)
        enfants_eligibles = eligible * menage.sum(
            enfant_a_charge_6_18, role=Menage.ENFANT
        )
        allocation_familiale = parameters(
            period
        ).prestations.non_contributives.allocation_familiale
        return enfants_eligibles * allocation_familiale


class transfert_monetaire_permanent_eligibilite_score(Variable):
    value_type = bool
    entity = Menage
    label = "Ménage éligible au programme Amen social selon le modèle de ciblage"
    definition_period = MONTH

    def formula_2020(menage, period, parameters):
        # Avant la circulaire n° 12 de 2022 (modèle de ciblage par décile), seuls
        # les critères primaires du décret 2020-317 ouvrent le droit. Sans cette
        # formule, le modèle ne rend aucun TMP éligible avant juin 2022.
        return menage("amen_social_eligible", period)

    def formula_2022_06(menage, period, parameters):
        decile = parameters(period).prestations.non_contributives.amen_social.decile
        return menage("amen_social_eligible", period) + (
            menage("amen_social_score_decile", period) <= decile
        )


class transfert_monetaire_permanent(Variable):
    value_type = float
    entity = Menage
    label = "Transfert monétaire permanent mensuel du programme Amen social"
    definition_period = MONTH

    def formula_2020(menage, period, parameters):
        amen_social = parameters(period).prestations.non_contributives.amen_social
        supplements = amen_social.supplements
        eligible = menage("transfert_monetaire_permanent_eligible", period)
        enfants_a_charge = menage("amen_social_enfants_a_charge", period)
        enfants_handicapes_a_charge = menage(
            "amen_social_enfants_handicapes_a_charge", period
        )
        return eligible * (
            amen_social.allocation_base
            + enfants_a_charge * supplements.enfant_a_charge
            + enfants_handicapes_a_charge
            * supplements.enfant_a_charge
            * supplements.handicap
        )


def make_param_reform(allocation_base: float, supplement_enfant: float):
    """Fabrique une réforme paramétrique (axe F1) : remplace l'allocation de base
    et le supplément par enfant à charge du TMP par des valeurs choisies, pour
    simuler l'effet d'un changement de barème. À appliquer **au-dessus** de
    `amen_social_corrections`. Le calcul reste celui du moteur.
    """
    from openfisca_core.periods import period as make_period

    def modifier(parameters):
        node = parameters.prestations.non_contributives.amen_social
        node.allocation_base.update(
            period=make_period("year:2020:10"), value=float(allocation_base)
        )
        node.supplements.enfant_a_charge.update(
            period=make_period("year:2020:10"), value=float(supplement_enfant)
        )
        return parameters

    class ParamReform(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=modifier)

    return ParamReform


class amen_social_corrections(Reform):
    """Déclare le décile de ciblage et corrige le nom de paramètre du TMP."""

    def apply(self):
        self.add_variable(amen_social_score_decile)
        self.add_variable(amen_social_seuil_revenu)
        self.add_variable(pnafn_eligible)
        self.update_variable(transfert_monetaire_permanent_eligibilite_score)
        self.update_variable(transfert_monetaire_permanent)
        self.update_variable(allocation_familiale_non_contributive_6_18)
