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
    AIDES,
    DIAGNOSTIC,
    HANDICAP,
    SORTIES,
    api_disponible,
    calculer,
    calculer_tmp_reforme,
    construire_situation,
    expliquer_eligibilite,
)
from i18n import LANGUES, t

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
    ui.tags.script(
        "Shiny.addCustomMessageHandler('setdir', function(m){"
        "document.documentElement.setAttribute('dir', m.dir);"
        "document.documentElement.setAttribute('lang', m.lang);});"
    ),
    ui.input_select("lang", "Langue / اللغة", LANGUES, selected="fr"),
    ui.output_ui("titre_app"),
    ui.output_ui("intro_ui"),
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
                ui.output_ui("enfants_help_ui"),
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
            ui.output_ui("avance_help_ui"),
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
    ui.hr(),
    ui.output_ui("entete"),
    ui.output_ui("titre_estimation"),
    ui.output_ui("resume"),
    ui.download_button("export_pdf", "PDF ⭳", class_="btn-sm"),
    ui.hr(),
    ui.input_action_button(
        "calculer",
        "Afficher le graphique et le comparateur",
        class_="btn-secondary",
    ),
    ui.card(
        ui.output_ui("graphe_header_ui"),
        ui.output_plot("courbe_aides", height="320px"),
    ),
    ui.accordion(
        ui.accordion_panel(
            "Comparateur par année (évolution du barème, situation constante)",
            ui.output_data_frame("comparateur"),
            value="p_comp",
        ),
        ui.accordion_panel(
            "Simuler une réforme du barème",
            ui.output_ui("reforme_help_ui"),
            ui.input_slider("ref_base", "Allocation de base réformée (DT/mois)",
                            min=0, max=600, value=260, step=10),
            ui.input_slider("ref_supp", "Supplément réformé par enfant (DT)",
                            min=0, max=50, value=10, step=5),
            ui.output_ui("reforme_effet"),
            value="p_reforme",
        ),
        ui.accordion_panel(
            "Détails (toutes les variables calculées)",
            ui.output_data_frame("details"),
            value="p_details",
        ),
        open=False,
        id="acc_details",
    ),
    ui.output_ui("footer_ui"),
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

    # ------------------------------------------------------------------ i18n
    def _lang() -> str:
        return str(input.lang() or "fr")

    @reactive.effect
    def _appliquer_langue():
        lang = _lang()
        oui_non = {"non": t("opt_non", lang), "oui": t("opt_oui", lang)}
        ui.update_select("annee", label=t("q_annee", lang))
        ui.update_numeric("nb_adultes", label=t("q_nb_adultes", lang))
        ui.update_numeric("nb_enfants", label=t("q_nb_enfants", lang))
        ui.update_numeric("revenu", label=t("q_revenu", lang))
        ui.update_numeric("decile", label=t("q_decile", lang))
        for cid, cle in (("residence", "q_residence"), ("achat", "q_achat"),
                         ("amg1", "q_amg1"), ("amg2", "q_amg2"), ("pnafn", "q_pnafn")):
            ui.update_radio_buttons(cid, label=t(cle, lang), choices=oui_non,
                                    selected=str(input[cid]()), inline=True)
        ui.update_action_button("calculer", label=t("btn_detail", lang))
        # Titres des panneaux (entonnoir + bas de page).
        ui.update_accordion_panel("form_acc", "p_foyer", title=t("step_foyer", lang))
        ui.update_accordion_panel("form_acc", "p_ressources", title=t("step_ressources", lang))
        ui.update_accordion_panel("form_acc", "p_biens", title=t("step_biens", lang))
        ui.update_accordion_panel("form_acc", "p_avance", title=t("step_avance", lang))
        ui.update_accordion_panel("acc_details", "p_comp", title=t("comparateur_header", lang))
        ui.update_accordion_panel("acc_details", "p_reforme", title=t("reforme_titre", lang))
        ui.update_accordion_panel("acc_details", "p_details", title=t("details_header", lang))
        ui.update_slider("ref_base", label=t("reforme_base", lang))
        ui.update_slider("ref_supp", label=t("reforme_supp", lang))
        # Sens de lecture (RTL en arabe).
        direction = "rtl" if lang == "ar" else "ltr"
        session.send_custom_message("setdir", {"dir": direction, "lang": lang})

    @render.ui
    def titre_app():
        return ui.h3(t("app_title", _lang()))

    @render.ui
    def intro_ui():
        return ui.markdown(t("intro", _lang()))

    @render.ui
    def enfants_help_ui():
        return ui.markdown(t("enfants_help", _lang()))

    @render.ui
    def avance_help_ui():
        return ui.markdown("*" + t("avance_help", _lang()) + "*")

    @render.ui
    def titre_estimation():
        return ui.markdown(t("votre_estimation", _lang()))

    @render.ui
    def graphe_header_ui():
        return ui.card_header(t("graphe_header", _lang()))

    @render.ui
    def footer_ui():
        return ui.markdown(t("footer", _lang()))

    @render.ui
    def reforme_help_ui():
        return ui.markdown(t("reforme_help", _lang()))

    @render.ui
    def reforme_effet():
        statut, contenu = resultat()
        lang = _lang()
        if statut != "ok":
            return ui.markdown("—")
        annee = int(input.annee())
        tmp_actuel = contenu.get("transfert_monetaire_permanent") or 0.0
        try:
            sit = _situation(float(input.revenu() or 0), annee)
            tmp_ref = calculer_tmp_reforme(
                sit, annee=annee,
                allocation_base=float(input.ref_base()),
                supplement_enfant=float(input.ref_supp()),
            ) or 0.0
        except RuntimeError as err:
            return ui.div(ui.markdown(str(err)), class_="alert alert-warning")
        ecart = tmp_ref - tmp_actuel

        def num(x):
            return f"{x:,.3f}".replace(",", " ")

        signe = "+" if ecart >= 0 else "−"
        couleur = "text-success" if ecart > 0 else ("text-danger" if ecart < 0 else "")
        unite = " \u062f.\u062a" if lang == "ar" else " DT"
        lignes = [
            (t("reforme_actuel", lang), num(tmp_actuel) + unite, ""),
            (t("reforme_nouveau", lang), num(tmp_ref) + unite, "font-weight:700;"),
            (t("reforme_ecart", lang), f"{signe} {num(abs(ecart))}{unite}/mois", ""),
        ]
        rows = [
            ui.tags.tr(
                ui.tags.td(lib, style=st),
                ui.tags.td(val, style=f"text-align:right;{st}",
                           class_=couleur if lib == t("reforme_ecart", lang) else ""),
            )
            for lib, val, st in lignes
        ]
        return ui.tags.table(ui.tags.tbody(*rows), class_="table table-sm")

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
            t("entete_tpl", _lang()).format(
                annee=input.annee(), taille=taille, adultes=nb_adultes,
                enfants=nb_enfants, revenu=input.revenu(),
            )
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
    def resultat():
        # Estimation **instantanée** : se recalcule à chaque réponse, sans clic.
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

        lang = _lang()
        res = contenu
        eligible = bool(res.get("transfert_monetaire_permanent_eligible"))
        tmp = res.get("transfert_monetaire_permanent") or 0.0

        def num(x):
            return f"{x:,.3f}".replace(",", " ")

        def dt(x):
            unite = " \u062f.\u062a" if lang == "ar" else " DT"
            return ("—" if x is None else num(x)) + unite

        if eligible:
            bandeau = ui.div(
                ui.markdown(t("banniere_eligible", lang).format(mt=num(tmp), an=num(tmp * 12))),
                class_="alert alert-success",
            )
        else:
            bandeau = ui.div(
                ui.markdown(t("banniere_non_eligible", lang)),
                class_="alert alert-info",
            )

        explication = expliquer_eligibilite(
            res,
            residence_secondaire=_oui(input.residence()),
            achat_onereux=_oui(input.achat()),
            score_decile=int(input.decile() or 11),
        )
        items = []
        for raison in explication["raisons"]:
            params = {
                k: (dt(v) if k in ("revenu", "seuil", "ecart") and isinstance(v, float) else v)
                for k, v in raison.items() if k != "code"
            }
            items.append(ui.tags.li(t(raison["code"], lang).format(**params)))
        if explication["eligible"]:
            voie = t(explication["voie_code"], lang) if explication["voie_code"] else ""
            titre_exp = t("exp_titre_oui", lang).format(voie=voie)
        else:
            titre_exp = t("exp_titre_non", lang)
        carte_explication = ui.card(
            ui.card_header(titre_exp),
            ui.tags.ul(*items),
        )

        # D3 — anti-non-recours.
        ouvre_des_droits = explication["eligible"] or (
            (res.get("total_aides_mensuel") or 0.0) > 0
        )
        if ouvre_des_droits:
            carte_demarche = ui.card(
                ui.card_header(t("d3_titre_oui", lang)),
                ui.markdown(t("d3_corps_oui", lang)),
                class_="border-success",
            )
        else:
            carte_demarche = ui.card(
                ui.card_header(t("d3_titre_non", lang)),
                ui.markdown(t("d3_corps_non", lang)),
                class_="border-info",
            )

        total = res.get("total_aides_mensuel") or 0.0
        bandeau_total = ui.div(
            ui.markdown(t("banniere_total", lang).format(mt=num(total), an=num(total * 12))),
            class_="alert alert-primary",
        )

        def _table(entrees, fort_cles=()):
            rows = []
            for cle, libelle, unite in entrees:
                fort = cle in fort_cles
                style = "font-weight:700;" if fort else ""
                rows.append(
                    ui.tags.tr(
                        ui.tags.td(t(cle, lang), style=style),
                        ui.tags.td(
                            _fmt(res.get(cle), unite),
                            style=f"text-align:right;{style}",
                        ),
                    )
                )
            return ui.tags.table(ui.tags.tbody(*rows), class_="table table-sm")

        # Mener avec les aides (ce que le foyer reçoit) ; reléguer le diagnostic
        # technique (revenu, seuil, éligibilités intermédiaires) dans un repli.
        aides_entrees = [(c, lib, "DT") for c, lib, _, _ in AIDES] + [
            ("total_aides_mensuel", "TOTAL des aides (mensuel)", "DT")
        ]
        return ui.TagList(
            bandeau,
            bandeau_total,
            carte_explication,
            carte_demarche,
            ui.card(
                ui.card_header(t("vos_aides", lang)),
                _table(
                    aides_entrees,
                    fort_cles=(
                        "transfert_monetaire_permanent",
                        "total_aides_mensuel",
                    ),
                ),
            ),
            ui.accordion(
                ui.accordion_panel(
                    t("detail_calcul", lang),
                    _table(list(DIAGNOSTIC)),
                ),
                open=False,
                id="acc_diag",
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
        lang = _lang()
        revenu = float(input.revenu() or 0)
        col_annee = t("col_annee", lang)
        col_alloc = t("allocation_familiale_non_contributive", lang)
        col_total = t("col_total", lang)
        lignes = []
        for annee in range(2021, 2027):
            try:
                res = calculer(_situation(revenu, annee), annee=annee)
            except httpx.HTTPError:
                continue
            lignes.append(
                {
                    col_annee: annee,
                    "TMP": _fmt(res.get("transfert_monetaire_permanent"), "DT"),
                    col_alloc: _fmt(
                        res.get("allocation_familiale_non_contributive"), "DT"
                    ),
                    col_total: _fmt(res.get("total_aides_mensuel"), "DT"),
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
