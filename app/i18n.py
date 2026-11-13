"""Internationalisation FR/AR du simulateur Amen social.

Dictionnaire plat `clé -> {"fr": …, "ar": …}` et `t(cle, lang)`. Couvre les
libellés statiques (barre latérale, en-têtes, bandeaux) et les libellés des
sorties (par clé de variable). Le texte dynamique de l'explication d'éligibilité
et les axes des graphiques restent en français (itération ultérieure).
"""

from __future__ import annotations

LANGUES = {"fr": "Français", "ar": "العربية"}

_STR: dict[str, dict[str, str]] = {
    # Général / barre latérale
    "app_title": {"fr": "Simulateur Amen social — Tunisie", "ar": "محاكي برنامج أمان الاجتماعي — تونس"},
    "langue": {"fr": "Langue / اللغة", "ar": "اللغة / Langue"},
    "annee": {"fr": "Année", "ar": "السنة"},
    "nb_adultes": {"fr": "Nombre d'adultes", "ar": "عدد البالغين"},
    "nb_enfants": {"fr": "Nombre d'enfants", "ar": "عدد الأطفال"},
    "generer": {"fr": "Générer / réinitialiser les enfants", "ar": "إنشاء / إعادة ضبط قائمة الأطفال"},
    "revenu": {"fr": "Revenu mensuel du ménage (DT)", "ar": "الدخل الشهري للأسرة (دينار)"},
    "residence": {"fr": "Possède une résidence secondaire", "ar": "يملك مسكنا ثانويا"},
    "achat": {"fr": "Achat/vente onéreux récent (> 30 × SMIG)", "ar": "عملية شراء أو بيع بقيمة مرتفعة مؤخرا (> 30 مرة الأجر الأدنى)"},
    "decile": {"fr": "Décile du score de ciblage (1 = plus pauvre ; 11 = hors ciblage)", "ar": "عشير نقاط الاستهداف (1 = الأفقر ؛ 11 = خارج الاستهداف)"},
    "cartes": {"fr": "Cartes / programmes détenus (saisie)", "ar": "البطاقات والبرامج المنتفَع بها"},
    "amg1": {"fr": "Titulaire carte AMG1 (gratuité des soins)", "ar": "حامل بطاقة العلاج المجاني (AMG1)"},
    "amg2": {"fr": "Titulaire carte AMG2 (tarif réduit)", "ar": "حامل بطاقة العلاج بتعريفة منخفضة (AMG2)"},
    "pnafn": {"fr": "Bénéficiaire PNAFN", "ar": "منتفع بالبرنامج الوطني لمساعدة العائلات المعوزة"},
    "calculer": {"fr": "Calculer", "ar": "احسب"},
    # En-têtes / cartes
    "enfants_header": {"fr": "Enfants (éditable : âge, étudiant, handicap, gluten, xeroderma)", "ar": "الأطفال (قابل للتعديل: السن، طالب، إعاقة، حساسية الغلوتين، جفاف الجلد المصطبغ)"},
    "resultat_header": {"fr": "Résultat du ménage — toutes les aides", "ar": "نتيجة الأسرة — جميع المساعدات"},
    "graphe_header": {"fr": "Total des aides selon le revenu mensuel du ménage", "ar": "مجموع المساعدات حسب الدخل الشهري للأسرة"},
    "comparateur_header": {"fr": "Comparateur par année (évolution du barème, situation constante)", "ar": "مقارنة حسب السنة (تطور السلّم، وضعية ثابتة)"},
    "details_header": {"fr": "Détails (toutes les variables calculées)", "ar": "تفاصيل (كل المتغيرات المحتسبة)"},
    "pdf_btn": {"fr": "Télécharger l'attestation (PDF)", "ar": "تحميل الشهادة (PDF)"},
    "pourquoi_oui": {"fr": "Pourquoi éligible", "ar": "لماذا مستحِق"},
    "pourquoi_non": {"fr": "Pourquoi non éligible", "ar": "لماذا غير مستحِق"},
    # Bandeaux
    "total_aides": {"fr": "Total des aides du ménage", "ar": "مجموع مساعدات الأسرة"},
    "par_mois": {"fr": "DT/mois", "ar": "دينار/شهر"},
    "eligible_tmp": {"fr": "Ménage éligible au transfert monétaire permanent", "ar": "الأسرة مستحِقة للتحويل النقدي القار"},
    "non_eligible_tmp": {"fr": "Ménage non éligible au transfert monétaire permanent", "ar": "الأسرة غير مستحِقة للتحويل النقدي القار"},
    # Libellés des sorties (par clé de variable)
    "amen_social_revenu": {"fr": "Revenu mensuel du ménage (sens Amen)", "ar": "الدخل الشهري للأسرة (بمفهوم أمان)"},
    "amen_social_seuil_revenu": {"fr": "Seuil de revenu applicable (critères primaires)", "ar": "سقف الدخل المعتمد (المعايير الأولية)"},
    "amen_social_presence_handicap_lourd": {"fr": "Présence d'un handicap lourd", "ar": "وجود إعاقة عميقة"},
    "amen_social_eligible": {"fr": "Éligible Amen (critères primaires, décret 2020-317)", "ar": "مستحِق لأمان (المعايير الأولية، الأمر 2020-317)"},
    "amen_social_enfants_a_charge": {"fr": "Enfants à charge (sens Amen)", "ar": "الأطفال المعالون (بمفهوم أمان)"},
    "amen_social_enfants_handicapes_a_charge": {"fr": "dont enfants handicapés", "ar": "منهم أطفال ذوو إعاقة"},
    "transfert_monetaire_permanent_eligible": {"fr": "Éligible au transfert monétaire permanent", "ar": "مستحِق للتحويل النقدي القار"},
    "transfert_monetaire_permanent": {"fr": "Transfert monétaire permanent", "ar": "التحويل النقدي القار"},
    "allocation_familiale_non_contributive": {"fr": "Allocation familiale (non contributive)", "ar": "المنحة العائلية (غير المساهماتية)"},
    "allocation_allergie_gluten": {"fr": "Allocation allergie au gluten", "ar": "منحة حساسية الغلوتين"},
    "allocation_xeroderma_pigmentosum": {"fr": "Allocation xeroderma pigmentosum", "ar": "منحة مرض جفاف الجلد المصطبغ"},
    "total_aides_mensuel": {"fr": "TOTAL des aides (mensuel)", "ar": "مجموع المساعدات (شهري)"},
}


def t(cle: str, lang: str = "fr") -> str:
    """Traduit une clé. Repli sur le français puis sur la clé brute."""
    entree = _STR.get(cle)
    if entree is None:
        return cle
    return entree.get(lang) or entree.get("fr") or cle
