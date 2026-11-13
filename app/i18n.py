"""Internationalisation FR/AR du simulateur Amen social.

Dictionnaire plat `clé -> {"fr": …, "ar": …}` et `t(cle, lang)`. Couvre les
libellés de la saisie (entonnoir), les en-têtes, bandeaux, l'explication
d'éligibilité (gabarits avec champs {…}) et les libellés des sorties.
"""

from __future__ import annotations

LANGUES = {"fr": "Français", "ar": "العربية"}

_STR: dict[str, dict[str, str]] = {
    # Général
    "app_title": {"fr": "Simulateur Amen social — Tunisie", "ar": "محاكي برنامج أمان الاجتماعي — تونس"},
    "lang_label": {"fr": "Langue / اللغة", "ar": "اللغة / Langue"},
    "intro": {
        "fr": "Répondez aux questions ci-dessous : votre estimation s'affiche en bas. Les **options avancées** sont facultatives.",
        "ar": "أجب عن الأسئلة التالية: يظهر تقديرك في الأسفل. **الخيارات المتقدمة** اختيارية.",
    },
    "opt_non": {"fr": "Non", "ar": "لا"},
    "opt_oui": {"fr": "Oui", "ar": "نعم"},
    # Étapes de l'entonnoir
    "step_foyer": {"fr": "① Votre foyer", "ar": "① أسرتك"},
    "step_ressources": {"fr": "② Vos ressources", "ar": "② مواردك"},
    "step_biens": {"fr": "③ Votre logement et vos biens", "ar": "③ سكنك وممتلكاتك"},
    "step_avance": {"fr": "④ Options avancées (facultatif)", "ar": "④ خيارات متقدمة (اختيارية)"},
    "q_annee": {"fr": "Année de la simulation", "ar": "سنة المحاكاة"},
    "q_nb_adultes": {"fr": "Combien d'adultes (18 ans et plus) vivent dans le foyer ?", "ar": "كم عدد البالغين (18 سنة فما فوق) في الأسرة؟"},
    "q_nb_enfants": {"fr": "Combien d'enfants (moins de 18 ans) vivent dans le foyer ?", "ar": "كم عدد الأطفال (دون 18 سنة) في الأسرة؟"},
    "enfants_help": {
        "fr": "**Précisez chaque enfant** (double-cliquez pour éditer) : âge, étudiant, handicap (Aucun / Léger / Lourd), et maladies donnant droit à une aide (gluten, xeroderma).",
        "ar": "**حدّد كل طفل** (انقر مرتين للتعديل): السن، طالب، إعاقة (لا شيء / خفيفة / عميقة)، وأمراض تخوّل منحة (الغلوتين، جفاف الجلد المصطبغ).",
    },
    "q_revenu": {"fr": "Revenu mensuel total du foyer (salaires + pensions de tous les membres), en dinars", "ar": "الدخل الشهري الجملي للأسرة (أجور + جرايات كل الأفراد)، بالدينار"},
    "q_residence": {"fr": "Le foyer possède-t-il un deuxième logement ?", "ar": "هل تملك الأسرة مسكنا ثانيا؟"},
    "q_achat": {"fr": "Un membre a-t-il acheté ou vendu un bien de grande valeur récemment (voiture, terrain… de plus de 30 fois le SMIG) ?", "ar": "هل اقتنى أو باع أحد الأفراد مؤخرا ملكا ذا قيمة مرتفعة (سيارة، أرض… تفوق 30 مرة الأجر الأدنى)؟"},
    "avance_help": {"fr": "À remplir seulement si vous connaissez ces informations. Sinon, laissez tel quel : ça ne bloque pas l'estimation.", "ar": "تُملأ فقط إذا كنت تعرف هذه المعطيات. وإلا اتركها كما هي: لا يعيق ذلك التقدير."},
    "q_amg1": {"fr": "Le foyer a-t-il une carte de soins gratuits (AMG1) ?", "ar": "هل للأسرة بطاقة علاج مجاني (AMG1)؟"},
    "q_amg2": {"fr": "… ou une carte de soins à tarif réduit (AMG2) ?", "ar": "… أو بطاقة علاج بتعريفة منخفضة (AMG2)؟"},
    "q_pnafn": {"fr": "Le foyer est-il bénéficiaire du PNAFN ?", "ar": "هل الأسرة منتفعة بالبرنامج الوطني لمساعدة العائلات المعوزة؟"},
    "q_decile": {"fr": "Décile du score de ciblage social, si connu (1 = plus modeste ; laissez 11 si inconnu)", "ar": "عشير نقاط الاستهداف الاجتماعي، إن عُرف (1 = الأفقر ؛ اترك 11 إذا كان غير معروف)"},
    # Boutons / sections
    "btn_detail": {"fr": "Afficher le graphique et le comparateur", "ar": "عرض الرسم البياني والمقارنة"},
    "votre_estimation": {"fr": "### Votre estimation", "ar": "### تقديرك"},
    "pdf_btn": {"fr": "Télécharger l'attestation (PDF)", "ar": "تحميل الشهادة (PDF)"},
    "graphe_header": {"fr": "Total des aides selon le revenu mensuel du ménage", "ar": "مجموع المساعدات حسب الدخل الشهري للأسرة"},
    "comparateur_header": {"fr": "Comparateur par année (évolution du barème, situation constante)", "ar": "مقارنة حسب السنة (تطوّر السلّم، وضعية ثابتة)"},
    "details_header": {"fr": "Détails (toutes les variables calculées)", "ar": "تفاصيل (كل المتغيرات المحتسبة)"},
    "vos_aides": {"fr": "Vos aides", "ar": "مساعداتك"},
    "detail_calcul": {"fr": "Détail du calcul (comment on arrive à ce résultat)", "ar": "تفصيل الحساب (كيف نصل إلى هذه النتيجة)"},
    "col_annee": {"fr": "Année", "ar": "السنة"},
    "col_total": {"fr": "Total aides", "ar": "مجموع المساعدات"},
    # En-tête dynamique
    "entete_tpl": {
        "fr": "**Année :** {annee} — **foyer de {taille} personne(s)** ({adultes} adulte(s), {enfants} enfant(s)) — **revenu** {revenu} DT/mois.",
        "ar": "**السنة:** {annee} — **أسرة من {taille} أشخاص** ({adultes} بالغ، {enfants} طفل) — **الدخل** {revenu} د.ت/شهر.",
    },
    # Bandeaux
    "banniere_eligible": {"fr": "✅ **Foyer éligible** au transfert monétaire permanent : **{mt} DT/mois** (soit {an} DT/an).", "ar": "✅ **الأسرة مستحِقة** للتحويل النقدي القار: **{mt} د.ت/شهر** (أي {an} د.ت/سنة)."},
    "banniere_non_eligible": {"fr": "ℹ️ **Foyer non éligible** au transfert monétaire permanent : ni les critères primaires (revenu/résidence/achat) ni le décile de ciblage ne sont remplis.", "ar": "ℹ️ **الأسرة غير مستحِقة** للتحويل النقدي القار: لم تتوفّر لا المعايير الأولية (الدخل/السكن/الاقتناء) ولا عشير الاستهداف."},
    "banniere_total": {"fr": "💰 **Total des aides du foyer : {mt} DT/mois** (soit {an} DT/an).", "ar": "💰 **مجموع مساعدات الأسرة: {mt} د.ت/شهر** (أي {an} د.ت/سنة)."},
    # Explication
    "exp_titre_oui": {"fr": "Pourquoi éligible — voie : {voie}", "ar": "لماذا مستحِق — المسلك: {voie}"},
    "exp_titre_non": {"fr": "Pourquoi non éligible", "ar": "لماذا غير مستحِق"},
    "v_primaire": {"fr": "critères primaires (décret 2020-317)", "ar": "المعايير الأولية (الأمر 2020-317)"},
    "v_decile": {"fr": "décile du score de ciblage", "ar": "عشير نقاط الاستهداف"},
    "r_revenu_sous_seuil": {"fr": "Revenu du foyer {revenu} ≤ seuil applicable {seuil}.", "ar": "دخل الأسرة {revenu} ≤ السقف المعتمد {seuil}."},
    "r_pas_exclusion": {"fr": "Pas de résidence secondaire, pas d'achat onéreux récent.", "ar": "لا مسكن ثانوي ولا اقتناء بقيمة مرتفعة مؤخرا."},
    "r_decile": {"fr": "Classé au décile {decile} du score de ciblage (≤ {seuil} ouvre le droit).", "ar": "مصنّف في العشير {decile} لنقاط الاستهداف (≤ {seuil} يفتح الحق)."},
    "r_res_secondaire": {"fr": "Exclu : le foyer possède une résidence secondaire.", "ar": "مُقصى: الأسرة تملك مسكنا ثانويا."},
    "r_achat": {"fr": "Exclu : achat/vente onéreux récent (> 30 × SMIG).", "ar": "مُقصى: اقتناء/بيع بقيمة مرتفعة مؤخرا (> 30 مرة الأجر الأدنى)."},
    "r_revenu_sur_seuil": {"fr": "Revenu du foyer {revenu} > seuil applicable {seuil} (dépasse de {ecart}).", "ar": "دخل الأسرة {revenu} > السقف المعتمد {seuil} (يتجاوزه بـ {ecart})."},
    "r_non_decile": {"fr": "Non classé au décile {seuil} du ciblage (décile saisi : {decile}).", "ar": "غير مصنّف في العشير {seuil} للاستهداف (العشير المُدخل: {decile})."},
    "r_aucun": {"fr": "Aucun critère d'éligibilité rempli.", "ar": "لم يتحقّق أي معيار استحقاق."},
    # D3 — anti-non-recours
    "d3_titre_oui": {"fr": "✅ Comment faire valoir vos droits", "ar": "✅ كيف تطالب بحقوقك"},
    "d3_corps_oui": {
        "fr": "Votre foyer **semble ouvrir des droits**. Cette estimation est indicative ; pour une décision officielle :\n\n- Déposez une demande à l'**unité locale de promotion sociale** de votre délégation (direction régionale des affaires sociales), ou inscrivez-vous au **registre social / plateforme Amen**.\n- Prévoyez une **pièce d'identité (CIN)** et les justificatifs de **revenus** et de **composition du foyer**.\n- Un **identifiant social unique** permet de **suivre la demande** et, en cas de refus, de déposer un **recours**.\n\n*Réf. : décret gouvernemental n° 2020-317 ; ministère des Affaires sociales (social.gov.tn).*",
        "ar": "يبدو أن أسرتك **قد تفتح حقوقا**. هذا التقدير إرشادي؛ وللحصول على قرار رسمي:\n\n- قدّم مطلبا لدى **الوحدة المحلية للنهوض الاجتماعي** بمعتمديتك (الإدارة الجهوية للشؤون الاجتماعية)، أو سجّل في **السجل الاجتماعي / منصة أمان**.\n- جهّز **بطاقة تعريف وطنية** وما يثبت **المداخيل** و**تركيبة الأسرة**.\n- يمكّنك **المعرّف الاجتماعي الوحيد** من **تتبّع المطلب**، وعند الرفض من تقديم **اعتراض**.\n\n*المرجع: الأمر الحكومي عدد 2020-317 ؛ وزارة الشؤون الاجتماعية (social.gov.tn).*",
    },
    "d3_titre_non": {"fr": "ℹ️ Que faire ensuite", "ar": "ℹ️ ماذا تفعل بعد ذلك"},
    "d3_corps_non": {
        "fr": "D'après vos réponses, votre foyer **ne semble pas remplir les critères** cette année. Vous pouvez néanmoins :\n\n- vous **inscrire au registre social** (votre situation peut évoluer, et l'inscription ouvre d'autres services) ;\n- demander un **réexamen / recours** auprès de l'unité locale de promotion sociale si vous estimez l'évaluation inexacte.\n\n*Cette estimation est indicative et ne remplace pas l'évaluation officielle.*",
        "ar": "حسب إجاباتك، يبدو أن أسرتك **لا تستوفي المعايير** هذه السنة. ومع ذلك يمكنك:\n\n- **التسجيل في السجل الاجتماعي** (وضعيتك قد تتغيّر، والتسجيل يفتح خدمات أخرى)؛\n- طلب **إعادة نظر / اعتراض** لدى الوحدة المحلية للنهوض الاجتماعي إذا رأيت التقييم غير دقيق.\n\n*هذا التقدير إرشادي ولا يعوّض التقييم الرسمي.*",
    },
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
    # F1 — simulation de réforme
    "reforme_titre": {"fr": "Simuler une réforme du barème (transfert monétaire permanent)", "ar": "محاكاة إصلاح السلّم (التحويل النقدي القار)"},
    "reforme_help": {"fr": "Déplacez les curseurs pour voir l'effet d'un autre barème sur **ce** foyer. Le calcul reste fait par le moteur.", "ar": "حرّك المؤشرات لرؤية أثر سلّم آخر على **هذه** الأسرة. يبقى الحساب بالمحرك."},
    "reforme_base": {"fr": "Allocation de base réformée (DT/mois)", "ar": "المنحة الأساسية بعد الإصلاح (د.ت/شهر)"},
    "reforme_supp": {"fr": "Supplément réformé par enfant à charge (DT)", "ar": "الزيادة بعد الإصلاح لكل طفل معال (د.ت)"},
    "reforme_actuel": {"fr": "TMP actuel (barème en vigueur)", "ar": "التحويل الحالي (السلّم الجاري)"},
    "reforme_nouveau": {"fr": "TMP sous la réforme", "ar": "التحويل حسب الإصلاح"},
    "reforme_ecart": {"fr": "Écart mensuel", "ar": "الفارق الشهري"},
    # Pied de page
    "footer": {
        "fr": "Calculé par le moteur **OpenFisca-Tunisia** (prestations non contributives, programme Amen social), avec une réforme corrective. Montants **mensuels** (DT/mois). Réf. : décret 2020-317 du 19 mai 2020 ; loi organique n° 2019-10. Estimation indicative, sans valeur de décision administrative.",
        "ar": "محسوب بمحرك **OpenFisca-Tunisia** (المنح غير المساهماتية، برنامج أمان الاجتماعي)، مع إصلاح تصحيحي. المبالغ **شهرية** (د.ت/شهر). المرجع: الأمر 2020-317 المؤرخ في 19 ماي 2020 ؛ القانون الأساسي عدد 2019-10. تقدير إرشادي لا قيمة قرارية إدارية له.",
    },
}


def t(cle: str, lang: str = "fr") -> str:
    """Traduit une clé. Repli sur le français puis sur la clé brute."""
    entree = _STR.get(cle)
    if entree is None:
        return cle
    return entree.get(lang) or entree.get("fr") or cle
