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

Cette réforme corrige les deux points **sans changer le barème** : elle déclare
`amen_social_score_decile` comme variable d'entrée (décile du score de ciblage,
1 = ménage le plus pauvre ; défaut 11 = hors ciblage) et redéfinit la formule du
TMP avec le bon nom de paramètre. Le calcul reste celui du modèle.

Les deux correctifs doivent être remontés en amont (voir
`docs/notes/desaccords.md` et `docs/notes/backlog.md`).
"""

from __future__ import annotations

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


class amen_social_corrections(Reform):
    """Déclare le décile de ciblage et corrige le nom de paramètre du TMP."""

    def apply(self):
        self.add_variable(amen_social_score_decile)
        self.update_variable(transfert_monetaire_permanent_eligibilite_score)
        self.update_variable(transfert_monetaire_permanent)
