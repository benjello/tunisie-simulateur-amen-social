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
    expliquer_eligibilite,
)

ANNEES = [str(a) for a in range(2020, 2027)]

# Libellé handicap -> valeur openfisca et inverse (pour la grille éditable).
HANDICAP_LIBELLE = {v: k for k, v in HANDICAP.items()}


def _grille_enfants(n: int) -> pd.DataFrame:
    """Grille initiale de n enfants (âge, étudiant, handicap, flags santé)."""
    return pd.DataFrame(
        {
            "Âge": [10] * n,
            "Étudiant": ["non"] * n,
            "Handicap": ["Aucun"] * n,
            "Gluten": ["non"] * n,
            "Xeroderma": ["non"] * n,
        }
    )


app_ui = ui.page_fillable(
    ui.h3("Simulateur Amen social — Tunisie"),
    ui.markdown(
        "Répondez aux questions ci-dessous : votre estimation s'affiche en bas. "
        "Les **options avancées** sont facultatives."
    ),
    ui.output_ui("statut_api"),
    ui.accordion(
        ui.accordion_panel(
            "① Votre foyer",
            ui.input_select("annee", "Année de la simulation", ANNEES, selected="2025"),
            ui.input_numeric(
                "nb_adultes",
                "Combien d'adultes (18 ans et plus) vivent dans le foyer ?",
                2, min=1, max=6, step=1,
            ),
            ui.input_numeric(
                "nb_enfants",
                "Combien d'enfants (moins de 18 ans) vivent dans le foyer ?",
                2, min=0, max=10, step=1,
            ),
            ui.panel_conditional(
                "input.nb_enfants > 0",
                ui.markdown(
                    "**Précisez chaque enfant** (double-cliquez pour éditer) : âge, "
                    "étudiant, handicap (Aucun / Léger / Lourd), et maladies "
                    "donnant droit à une aide (gluten, xeroderma)."
                ),
                ui.output_data_frame("grille"),
            ),
            value="p_foyer",
        ),
        ui.accordion_panel(
            "② Vos ressources",
            ui.input_numeric(
                "revenu",
                "Revenu mensuel total du foyer (salaires + pensions de tous les "
                "membres), en dinars",
                150, min=0, step=50,
            ),
            value="p_ressources",
        ),
        ui.accordion_panel(
            "③ Votre logement et vos biens",
            ui.input_radio_buttons(
                "residence",
                "Le foyer possède-t-il un deuxième logement ?",
                {"non": "Non", "oui": "Oui"}, selected="non", inline=True,
            ),
            ui.input_radio_buttons(
                "achat",
                "Un membre a-t-il acheté ou vendu un bien de grande valeur "
                "récemment (voiture, terrain… de plus de 30 fois le SMIG) ?",
                {"non": "Non", "oui": "Oui"}, selected="non", inline=True,
            ),
            value="p_biens",
        ),
        ui.accordion_panel(
            "④ Options avancées (facultatif)",
            ui.markdown(
                "*À remplir seulement si vous connaissez ces informations. "
                "Sinon, laissez tel quel : ça ne bloque pas l'estimation.*"
            ),
            ui.input_radio_buttons(
                "amg1", "Le foyer a-t-il une carte de soins gratuits (AMG1) ?",
                {"non": "Non", "oui": "Oui"}, selected="non", inline=True,
            ),
            ui.input_radio_buttons(
                "amg2", "… ou une carte de soins à tarif réduit (AMG2) ?",
                {"non": "Non", "oui": "Oui"}, selected="non", inline=True,
            ),
            ui.input_radio_buttons(
                "pnafn", "Le foyer est-il bénéficiaire du PNAFN ?",
                {"non": "Non", "oui": "Oui"}, selected="non", inline=True,
            ),
            ui.input_numeric(
                "decile",
                "Décile du score de ciblage social, si connu "
                "(1 = plus modeste ; laissez 11 si inconnu)",
                11, min=1, max=11, step=1,
            ),
            value="p_avance",
        ),
        id="form_acc",
        open=["p_foyer", "p_ressources", "p_biens"],
        multiple=True,
    ),
    ui.input_action_button(
        "calculer", "Voir mon estimation", class_="btn-primary btn-lg"
    ),
    ui.hr(),
    ui.output_ui("entete"),
    ui.output_ui("resume"),
    ui.download_button("export_pdf", "Télécharger l'attestation (PDF)", class_="btn-sm"),
    ui.card(
        ui.card_header("Total des aides selon le revenu mensuel du ménage"),
        ui.output_plot("courbe_aides", height="320px"),
    ),
    ui.accordion(
        ui.accordion_panel(
            "Comparateur par année (évolution du barème, situation constante)",
            ui.output_data_frame("comparateur"),
        ),
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


def _oui(valeur) -> bool:
    """Vrai si un bouton radio Oui/Non vaut « oui »."""
    return str(valeur).strip().lower() == "oui"


def server(input, output, session):
    enfants_rv = reactive.value(_grille_enfants(2))

    @reactive.effect
    @reactive.event(input.nb_enfants)
    def _ajuster_grille():
        # La grille suit automatiquement le nombre d'enfants (pas de bouton) :
        # on conserve les lignes déjà saisies et on ajoute/retire au besoin.
        n = int(input.nb_enfants() or 0)
        actuel = enfants_rv()
        if len(actuel) == n:
            return
        if n < len(actuel):
            enfants_rv.set(actuel.iloc[:n].reset_index(drop=True))
        else:
            surplus = _grille_enfants(n - len(actuel))
            enfants_rv.set(
                pd.concat([actuel, surplus], ignore_index=True)
            )

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
        def _oui(valeur) -> bool:
            return str(valeur).strip().lower() in ("oui", "yes", "true", "1")

        for _, r in df.iterrows():
            handicap = HANDICAP_LIBELLE.get(str(r["Handicap"]).strip(), 0)
            enfants.append(
                {
                    "age": int(r["Âge"]),
                    "etudiant": _oui(r["Étudiant"]),
                    "handicap": handicap,
                    "allergie_gluten": _oui(r.get("Gluten", "non")),
                    "xeroderma": _oui(r.get("Xeroderma", "non")),
                }
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

    def _situation(revenu: float, annee: int) -> dict:
        """Construit une situation à partir des entrées courantes, pour un revenu
        et une année donnés (réutilisé par le résumé, le graphe, le comparateur)."""
        return construire_situation(
            annee=annee,
            nb_adultes=int(input.nb_adultes() or 1),
            enfants=_enfants_saisis(),
            revenu_mensuel=float(revenu),
            residence_secondaire=_oui(input.residence()),
            achat_onereux=_oui(input.achat()),
            score_decile=int(input.decile() or 11),
            amg1=_oui(input.amg1()),
            amg2=_oui(input.amg2()),
            pnafn=_oui(input.pnafn()),
        )

    @reactive.calc
    @reactive.event(input.calculer, ignore_none=False)
    def resultat():
        annee = int(input.annee())
        try:
            situation = _situation(float(input.revenu() or 0), annee)
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

        explication = expliquer_eligibilite(
            res,
            residence_secondaire=_oui(input.residence()),
            achat_onereux=_oui(input.achat()),
            score_decile=int(input.decile() or 11),
        )
        items = [ui.tags.li(r) for r in explication["raisons"]]
        titre_exp = (
            f"Pourquoi éligible — voie : {explication['voie']}"
            if explication["eligible"]
            else "Pourquoi non éligible"
        )
        carte_explication = ui.card(
            ui.card_header(titre_exp),
            ui.tags.ul(*items),
        )

        # D3 — anti-non-recours : comment faire valoir ses droits.
        ouvre_des_droits = explication["eligible"] or (
            (res.get("total_aides_mensuel") or 0.0) > 0
        )
        if ouvre_des_droits:
            carte_demarche = ui.card(
                ui.card_header("✅ Comment faire valoir vos droits"),
                ui.markdown(
                    "Votre foyer **semble ouvrir des droits**. Cette estimation "
                    "est indicative ; pour une décision officielle :\n\n"
                    "- Déposez une demande à l'**unité locale de promotion sociale** "
                    "de votre délégation (direction régionale des affaires "
                    "sociales), ou inscrivez-vous au **registre social / "
                    "plateforme Amen**.\n"
                    "- Prévoyez une **pièce d'identité (CIN)** et les justificatifs "
                    "de **revenus** et de **composition du foyer**.\n"
                    "- Un **identifiant social unique** permet de **suivre la "
                    "demande** et, en cas de refus, de déposer un **recours**.\n\n"
                    "*Réf. : décret gouvernemental n° 2020-317 ; ministère des "
                    "Affaires sociales (social.gov.tn).*"
                ),
                class_="border-success",
            )
        else:
            carte_demarche = ui.card(
                ui.card_header("ℹ️ Que faire ensuite"),
                ui.markdown(
                    "D'après vos réponses, votre foyer **ne semble pas remplir "
                    "les critères** cette année. Vous pouvez néanmoins :\n\n"
                    "- vous **inscrire au registre social** (votre situation peut "
                    "évoluer, et l'inscription ouvre d'autres services) ;\n"
                    "- demander un **réexamen / recours** auprès de l'unité locale "
                    "de promotion sociale si vous estimez l'évaluation inexacte.\n\n"
                    "*Cette estimation est indicative et ne remplace pas "
                    "l'évaluation officielle.*"
                ),
                class_="border-info",
            )

        total = res.get("total_aides_mensuel") or 0.0
        bandeau_total = ui.div(
            ui.markdown(
                f"💰 **Total des aides du ménage : {total:,.3f} DT/mois**".replace(
                    ",", " "
                )
                + f" (soit {total * 12:,.3f} DT/an).".replace(",", " ")
            ),
            class_="alert alert-primary",
        )

        lignes = []
        for cle, libelle, unite in SORTIES:
            fort = cle in ("transfert_monetaire_permanent", "total_aides_mensuel")
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
            bandeau_total,
            carte_explication,
            carte_demarche,
            ui.card(
                ui.card_header("Résultat du ménage — toutes les aides"),
                ui.tags.table(ui.tags.tbody(*lignes), class_="table table-sm"),
            ),
        )

    @render.plot(alt="Total des aides selon le revenu du ménage")
    @reactive.event(input.calculer, ignore_none=False)
    def courbe_aides():
        import matplotlib.pyplot as plt

        annee = int(input.annee())
        revenus = list(range(0, 2001, 100))
        totaux = []
        for rev in revenus:
            try:
                res = calculer(_situation(rev, annee), annee=annee)
                totaux.append(res.get("total_aides_mensuel") or 0.0)
            except httpx.HTTPError:
                totaux.append(0.0)
        fig, ax = plt.subplots()
        ax.plot(revenus, totaux, color="#2a7", linewidth=2)
        ax.fill_between(revenus, totaux, color="#2a7", alpha=0.12)
        ax.set_xlabel("Revenu mensuel du ménage (DT)")
        ax.set_ylabel("Total des aides (DT/mois)")
        ax.set_title(f"Année {annee}")
        ax.grid(True, alpha=0.3)
        return fig

    @render.data_frame
    def comparateur():
        if not input.calculer():
            return render.DataGrid(pd.DataFrame({"Info": ["Lancez un calcul"]}))
        revenu = float(input.revenu() or 0)
        lignes = []
        for annee in range(2021, 2027):
            try:
                res = calculer(_situation(revenu, annee), annee=annee)
            except httpx.HTTPError:
                continue
            lignes.append(
                {
                    "Année": annee,
                    "TMP": _fmt(res.get("transfert_monetaire_permanent"), "DT"),
                    "Alloc. familiale NC": _fmt(
                        res.get("allocation_familiale_non_contributive"), "DT"
                    ),
                    "Total aides": _fmt(res.get("total_aides_mensuel"), "DT"),
                }
            )
        return render.DataGrid(pd.DataFrame(lignes), width="100%")

    @render.download(filename="attestation_amen_social.pdf")
    def export_pdf():
        import io

        import matplotlib.pyplot as plt

        statut, contenu = resultat()
        fig, ax = plt.subplots(figsize=(8, 7))
        ax.axis("off")
        if statut != "ok":
            ax.text(0.5, 0.5, "Aucune simulation calculée.", ha="center")
        else:
            res = contenu
            ax.set_title(
                f"Simulation Amen social — année {int(input.annee())}",
                fontsize=14, fontweight="bold",
            )
            y = 0.92
            for cle, libelle, unite in SORTIES:
                fort = cle in (
                    "transfert_monetaire_permanent",
                    "total_aides_mensuel",
                )
                ax.text(0.05, y, libelle, fontsize=10,
                        fontweight="bold" if fort else "normal")
                ax.text(0.95, y, _fmt(res.get(cle), unite), fontsize=10, ha="right",
                        fontweight="bold" if fort else "normal")
                y -= 0.05
            explication = expliquer_eligibilite(
                res,
                residence_secondaire=_oui(input.residence()),
                achat_onereux=_oui(input.achat()),
                score_decile=int(input.decile() or 11),
            )
            y -= 0.03
            titre_exp = (
                "Éligible — " + (explication["voie"] or "")
                if explication["eligible"]
                else "Non éligible"
            )
            ax.text(0.05, y, titre_exp, fontsize=11, fontweight="bold")
            y -= 0.045
            for r in explication["raisons"]:
                ax.text(0.07, y, f"• {r}", fontsize=9)
                y -= 0.04
            ax.text(0.05, 0.02,
                    "Calculé par OpenFisca-Tunisia — estimation indicative, sans "
                    "valeur de décision administrative.",
                    fontsize=8, style="italic", color="#666")
        buf = io.BytesIO()
        fig.savefig(buf, format="pdf")
        plt.close(fig)
        yield buf.getvalue()

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
