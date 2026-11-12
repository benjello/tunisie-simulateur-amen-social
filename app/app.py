"""Simulateur du programme Amen social (Tunisie).

Interface Shiny for Python. Aucun calcul n'est fait ici : la situation du ménage
est envoyée au moteur OpenFisca-Tunisia (via une petite réforme corrective, voir
`reform.py`), qui renvoie l'éligibilité et le montant du transfert monétaire
permanent (TMP).

Le programme Amen social (loi organique n° 2019-10, décret 2020-317) verse un
transfert mensuel aux ménages pauvres : une allocation de base, majorée par
enfant à charge et par enfant handicapé à charge. L'éligibilité suit soit les
critères primaires (revenu sous un seuil fonction de la taille du ménage, pas de
résidence secondaire, pas d'achat onéreux), soit le décile du score de ciblage.

Lancer en local (mode moteur en direct, défaut) :
    shiny run app/app.py --port 8102
"""

from __future__ import annotations

import httpx
import pandas as pd
from shiny import App, reactive, render, ui

from openfisca_client import (
    HANDICAP,
    SORTIES,
    api_disponible,
    calculer,
    construire_situation,
)

ANNEES = [str(a) for a in range(2020, 2027)]

# Libellé handicap -> valeur openfisca et inverse (pour la grille éditable).
HANDICAP_LIBELLE = {v: k for k, v in HANDICAP.items()}


def _grille_enfants(n: int) -> pd.DataFrame:
    """Grille initiale de n enfants (âge, étudiant, handicap)."""
    return pd.DataFrame(
        {
            "Âge": [10] * n,
            "Étudiant": ["non"] * n,
            "Handicap": ["Aucun"] * n,
        }
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("annee", "Année", ANNEES, selected="2025"),
        ui.input_numeric("nb_adultes", "Nombre d'adultes", 2, min=1, max=6, step=1),
        ui.input_numeric("nb_enfants", "Nombre d'enfants", 2, min=0, max=10, step=1),
        ui.input_action_button(
            "generer", "Générer / réinitialiser les enfants",
            class_="btn-secondary btn-sm",
        ),
        ui.hr(),
        ui.input_numeric(
            "revenu", "Revenu mensuel du ménage (DT)", 150, min=0, step=50
        ),
        ui.input_checkbox("residence", "Possède une résidence secondaire", False),
        ui.input_checkbox(
            "achat", "Achat/vente onéreux récent (> 30 × SMIG)", False
        ),
        ui.input_numeric(
            "decile",
            "Décile du score de ciblage (1 = plus pauvre ; 11 = hors ciblage)",
            11, min=1, max=11, step=1,
        ),
        ui.hr(),
        ui.input_action_button("calculer", "Calculer", class_="btn-primary"),
        width=360,
    ),
    ui.h3("Simulateur Amen social — Tunisie"),
    ui.output_ui("statut_api"),
    ui.output_ui("entete"),
    ui.panel_conditional(
        "input.nb_enfants > 0",
        ui.card(
            ui.card_header("Enfants (éditable : âge, étudiant oui/non, handicap)"),
            ui.output_data_frame("grille"),
            ui.markdown(
                "*Handicap : « Aucun », « Léger » ou « Lourd ». Un enfant à charge "
                "est compté de 6 à 18 ans (25 ans si étudiant), ou à tout âge s'il "
                "est lourdement handicapé.*"
            ),
        ),
    ),
    ui.output_ui("resume"),
    ui.accordion(
        ui.accordion_panel(
            "Détails (toutes les variables calculées)",
            ui.output_data_frame("details"),
        ),
        open=False,
        id="acc_details",
    ),
    ui.markdown(
        "Calculé par le moteur **OpenFisca-Tunisia** (prestations non "
        "contributives, programme Amen social), avec une réforme corrective "
        "(`reform.py`). Montants **mensuels** (DT/mois). Barème : allocation de "
        "base + 10 DT/enfant à charge + 20 DT/enfant handicapé à charge "
        "(majoration × 2). Référence : décret 2020-317 du 19 mai 2020 ; loi "
        "organique n° 2019-10."
    ),
    title="Simulateur Amen social Tunisie",
)


def _fmt(valeur, unite: str) -> str:
    if valeur is None:
        return "—"
    if unite == "bool":
        return "oui" if valeur else "non"
    if unite == "int":
        return f"{int(round(valeur))}"
    return f"{valeur:,.3f} DT".replace(",", " ")


def server(input, output, session):
    enfants_rv = reactive.value(_grille_enfants(2))

    @reactive.effect
    @reactive.event(input.generer)
    def _regenere():
        enfants_rv.set(_grille_enfants(int(input.nb_enfants() or 0)))

    @render.data_frame
    def grille():
        return render.DataGrid(enfants_rv(), editable=True, width="100%")

    @render.ui
    def statut_api():
        if api_disponible():
            return ui.TagList()
        return ui.div(
            ui.markdown(
                "⚠️ **API OpenFisca Amen social injoignable.** Démarrez-la avec "
                "la réforme :\n\n"
                "```\nopenfisca serve -c openfisca_tunisia "
                "-r reform.amen_social_corrections -p 5002\n```\n"
                "ou utilisez le mode moteur en direct (`OPENFISCA_MODE=local`)."
            ),
            class_="alert alert-warning",
        )

    def _enfants_saisis() -> list[dict]:
        if int(input.nb_enfants() or 0) <= 0:
            return []
        df = grille.data_view()
        enfants = []
        for _, r in df.iterrows():
            etu = str(r["Étudiant"]).strip().lower() in ("oui", "yes", "true", "1")
            handicap = HANDICAP_LIBELLE.get(str(r["Handicap"]).strip(), 0)
            enfants.append(
                {"age": int(r["Âge"]), "etudiant": etu, "handicap": handicap}
            )
        return enfants

    @render.ui
    def entete():
        nb_adultes = int(input.nb_adultes() or 1)
        nb_enfants = int(input.nb_enfants() or 0)
        taille = nb_adultes + nb_enfants
        return ui.markdown(
            f"**Année :** {input.annee()} — **ménage de {taille} personne(s)** "
            f"({nb_adultes} adulte(s), {nb_enfants} enfant(s)) — "
            f"**revenu** {input.revenu()} DT/mois."
        )

    @reactive.calc
    @reactive.event(input.calculer, ignore_none=False)
    def resultat():
        annee = int(input.annee())
        situation = construire_situation(
            annee=annee,
            nb_adultes=int(input.nb_adultes() or 1),
            enfants=_enfants_saisis(),
            revenu_mensuel=float(input.revenu() or 0),
            residence_secondaire=bool(input.residence()),
            achat_onereux=bool(input.achat()),
            score_decile=int(input.decile() or 11),
        )
        try:
            return ("ok", calculer(situation, annee=annee))
        except httpx.HTTPError as erreur:
            return ("erreur", str(erreur))

    @render.ui
    def resume():
        statut, contenu = resultat()
        if statut == "erreur":
            return ui.div(
                ui.markdown(f"**Erreur de calcul :** {contenu}"),
                class_="alert alert-danger",
            )

        res = contenu
        eligible = bool(res.get("transfert_monetaire_permanent_eligible"))
        tmp = res.get("transfert_monetaire_permanent") or 0.0

        if eligible:
            bandeau = ui.div(
                ui.markdown(
                    f"✅ **Ménage éligible** au transfert monétaire permanent : "
                    f"**{tmp:,.3f} DT/mois**".replace(",", " ")
                    + f" (soit {tmp * 12:,.3f} DT/an).".replace(",", " ")
                ),
                class_="alert alert-success",
            )
        else:
            bandeau = ui.div(
                ui.markdown(
                    "ℹ️ **Ménage non éligible** au transfert monétaire permanent : "
                    "ni les critères primaires (revenu/résidence/achat) ni le "
                    "décile de ciblage ne sont remplis."
                ),
                class_="alert alert-info",
            )

        lignes = []
        for cle, libelle, unite in SORTIES:
            fort = cle == "transfert_monetaire_permanent"
            style = "font-weight:700;" if fort else ""
            lignes.append(
                ui.tags.tr(
                    ui.tags.td(libelle, style=style),
                    ui.tags.td(
                        _fmt(res.get(cle), unite),
                        style=f"text-align:right;{style}",
                    ),
                )
            )
        return ui.TagList(
            bandeau,
            ui.card(
                ui.card_header("Résultat du ménage"),
                ui.tags.table(ui.tags.tbody(*lignes), class_="table table-sm"),
            ),
        )

    @render.data_frame
    def details():
        statut, contenu = resultat()
        if statut != "ok":
            return render.DataGrid(pd.DataFrame({"Info": ["Aucun calcul"]}))
        df = pd.DataFrame(
            [
                {
                    "Variable": cle,
                    "Libellé": libelle,
                    "Valeur": _fmt(contenu.get(cle), unite),
                }
                for cle, libelle, unite in SORTIES
            ]
        )
        return render.DataGrid(df, width="100%")


app = App(app_ui, server)
