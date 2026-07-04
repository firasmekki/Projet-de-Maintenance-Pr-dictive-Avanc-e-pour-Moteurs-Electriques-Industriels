"""
ORBIT AI — Base de connaissances industrielle.
Couvre : ISO 10816/20816, IEC 60034, IEEE 112, défauts moteurs.
"""
from __future__ import annotations

KNOWLEDGE_BASE: list[dict] = [

    # ── ISO 10816 ────────────────────────────────────────────────────────
    {
        "id": "iso_10816_zones",
        "title": "ISO 10816 — Zones de vibration (moteurs > 15 kW)",
        "keywords": ["vibration", "iso 10816", "rms", "seuil", "zone", "mm/s", "alarme", "danger", "limite"],
        "category": "norm",
        "content": (
            "ISO 10816 définit 4 zones pour les moteurs électriques > 15 kW sur paliers rigides:\n"
            "• Zone A (Neuf / révisé) : < 2,3 mm/s RMS — état acceptable\n"
            "• Zone B (Fonctionnement long terme) : 2,3 à 4,5 mm/s — surveillance recommandée\n"
            "• Zone C (Alarme) : 4,5 à 7,1 mm/s — maintenance à planifier rapidement\n"
            "• Zone D (Danger) : > 7,1 mm/s — arrêt immédiat recommandé, risque de dommages\n"
            "Pour moteurs < 15 kW, les seuils sont légèrement inférieurs (Zone D > 4,5 mm/s)."
        ),
    },
    {
        "id": "iso_20816_update",
        "title": "ISO 20816 — Mise à jour ISO 10816",
        "keywords": ["iso 20816", "vibration", "norme", "récente", "2016"],
        "category": "norm",
        "content": (
            "ISO 20816 (2016) remplace ISO 10816. Elle introduit:\n"
            "• Mesures sur le palier ET le carter\n"
            "• Distinction entre vibrations relatives et absolues\n"
            "• Seuils adaptés par type de machine (montage rigide vs flexible)\n"
            "Les seuils de Zone D restent similaires: > 7,1 mm/s pour moteurs industriels > 15 kW."
        ),
    },

    # ── IEC 60034 ────────────────────────────────────────────────────────
    {
        "id": "iec_60034_efficiency",
        "title": "IEC 60034-30 — Classes de rendement moteur IE1 à IE4",
        "keywords": ["iec 60034", "rendement", "efficacité", "ie1", "ie2", "ie3", "ie4", "consommation", "énergie"],
        "category": "norm",
        "content": (
            "IEC 60034-30 définit les classes de rendement:\n"
            "• IE1 (Standard) : rendement de base, interdit dans l'UE depuis 2017\n"
            "• IE2 (Haut rendement) : +2 à 3% vs IE1\n"
            "• IE3 (Premium) : obligatoire UE pour > 0,75 kW depuis 2015\n"
            "• IE4 (Super Premium) : gains supplémentaires, moteurs à aimants permanents\n"
            "Un moteur en surcharge consomme au-delà de sa plage nominale (cos φ chute, courant augmente)."
        ),
    },
    {
        "id": "iec_60034_temperature",
        "title": "IEC 60034-1 — Classes d'isolation thermique",
        "keywords": ["température", "isolation", "classe", "thermique", "surchauffe", "bobinage", "iec 60034"],
        "category": "norm",
        "content": (
            "IEC 60034-1 définit les classes d'isolation par température maximale admissible:\n"
            "• Classe A : 105°C (température ambiante 40°C + échauffement 65°C)\n"
            "• Classe B : 130°C — la plus courante\n"
            "• Classe F : 155°C — moteurs hautes performances\n"
            "• Classe H : 180°C — applications sévères\n"
            "Règle empirique: chaque +10°C réduit la durée de vie d'isolation de 50%.\n"
            "Un moteur opérant > 90°C en classe B est en danger d'isolation prématurée."
        ),
    },

    # ── IEEE 112 ────────────────────────────────────────────────────────
    {
        "id": "ieee_112_testing",
        "title": "IEEE 112 — Tests de rendement moteurs asynchrones",
        "keywords": ["ieee 112", "test", "rendement", "essai", "mesure", "puissance"],
        "category": "norm",
        "content": (
            "IEEE 112 définit les méthodes standardisées de mesure du rendement:\n"
            "• Méthode A: Mesure directe entrée/sortie (simple mais imprécis)\n"
            "• Méthode B: Mesure des pertes séparées (recommandée)\n"
            "• Méthode E: Mesure de l'impédance à faible tension\n"
            "• Méthode F: Dynanomètre sur charge variable\n"
            "Utiliser IEEE 112 Méthode B pour comparer le rendement actuel vs nominal."
        ),
    },

    # ── Défauts moteurs ──────────────────────────────────────────────────
    {
        "id": "bearing_wear",
        "title": "Usure des Roulements — Diagnostic et prévention",
        "keywords": ["roulement", "bearing", "bpfi", "bpfo", "usure", "fréquence", "caractéristique", "diagnostic"],
        "category": "fault",
        "content": (
            "L'usure des roulements représente ~40% des défaillances moteur.\n"
            "Signatures:\n"
            "• Vibrations aux fréquences caractéristiques: BPFI (bague intérieure), BPFO (bague extérieure), BSF (billes)\n"
            "• Élévation progressive de température (frottement)\n"
            "• Bruit aigu ou choc périodique\n"
            "Stades d'évolution:\n"
            "1. Micro-fissures: détectable par ultrasons uniquement\n"
            "2. Pitting: visible en spectre FFT\n"
            "3. Usure avancée: amplitude vibratoire > 5 mm/s\n"
            "4. Défaillance: amplitude > 7 mm/s, ISO Zone D\n"
            "Formule L10 (durée de vie): L10 = (C/P)³ × 10⁶/60n [heures]\n"
            "où C=charge dynamique nominale, P=charge appliquée, n=vitesse (tr/min).\n"
            "Correction: Inspecter et lubrifier. Remplacement si Zone C atteinte."
        ),
    },
    {
        "id": "misalignment",
        "title": "Désalignement — Types et détection",
        "keywords": ["désalignement", "alignement", "couplage", "arbre", "angulaire", "parallèle"],
        "category": "fault",
        "content": (
            "Le désalignement cause ~35% des défaillances prématurées de roulements.\n"
            "Types:\n"
            "• Angulaire: angle entre les axes des arbres\n"
            "• Parallèle: décalage latéral entre axes\n"
            "• Combiné: les deux simultanément\n"
            "Signatures vibratoires:\n"
            "• Vibrations à 2× RPM dominantes (désalignement angulaire)\n"
            "• Forte composante axiale (ratio axiale/radiale > 0,5)\n"
            "• Harmoniques à 1×, 2×, 3× RPM\n"
            "Seuil: > ±0,05 mm nécessite realignement laser.\n"
            "Correction: Alignement laser ± 0,05 mm en angulaire et parallèle."
        ),
    },
    {
        "id": "unbalance",
        "title": "Déséquilibre Rotor — Causes et correction",
        "keywords": ["déséquilibre", "unbalance", "rotor", "balancement", "masse", "centrifuge"],
        "category": "fault",
        "content": (
            "Le déséquilibre rotor génère des forces centrifuges périodiques.\n"
            "Signatures:\n"
            "• Vibration dominante à 1× RPM (fréquence de rotation)\n"
            "• Amplitude proportionnelle au carré de la vitesse\n"
            "• Pas de composante axiale significative\n"
            "• Températures dans les normes\n"
            "ISO 1940-1 définit les grades d'équilibrage:\n"
            "• G1: instruments de précision\n"
            "• G2.5: moteurs électriques industriels (standard)\n"
            "• G6.3: pompes, ventilateurs\n"
            "Correction: Équilibrage statique puis dynamique. Nettoyer les aubes du ventilateur."
        ),
    },
    {
        "id": "rotor_fault",
        "title": "Défaut Rotor — Barres cassées et excentricité",
        "keywords": ["rotor", "barre", "cassée", "excentricité", "glissement", "courant", "mca"],
        "category": "fault",
        "content": (
            "Les défauts rotor incluent les barres cassées et l'excentricité.\n"
            "Barres cassées — signatures électriques:\n"
            "• Bandes latérales autour de la fréquence fondamentale: f ± 2s×f (s=glissement)\n"
            "• Oscillation de courant à la fréquence de glissement\n"
            "• Hausse du courant moyen (+5 à 15%)\n"
            "Excentricité — signatures vibratoires:\n"
            "• Vibrations à la fréquence de passage des pôles rotoriques\n"
            "• UMP (Unbalanced Magnetic Pull) alternant\n"
            "Diagnostic: MCSA (Motor Current Signature Analysis) — analyse FFT du courant.\n"
            "Correction: Inspection des barres de cage, rembobinage si nécessaire."
        ),
    },
    {
        "id": "insulation_fault",
        "title": "Défaut d'Isolation — Dégradation des bobinages",
        "keywords": ["isolation", "bobinage", "résistance", "megohmmètre", "claquage", "humidité", "thermique"],
        "category": "fault",
        "content": (
            "La dégradation d'isolation est la principale cause d'arrêt long terme.\n"
            "Causes:\n"
            "• Thermique: chaque +10°C divise la durée de vie par 2 (loi d'Arrhenius)\n"
            "• Humidité: absorption d'eau → réduction résistance d'isolation\n"
            "• Vibrations: fatigue mécanique des bobinages\n"
            "• Harmoniques: contraintes diélectriques supplémentaires\n"
            "Mesures:\n"
            "• Résistance d'isolation: > 100 MΩ (normal), 1-100 MΩ (surveillance), < 1 MΩ (critique)\n"
            "• Indice de polarisation IP: > 2 (bon), 1-2 (acceptable), < 1 (critique)\n"
            "• Test DAR (Dielectric Absorption Ratio): IP = R10min / R1min\n"
            "Correction: Séchage, nettoyage, re-vernissage ou rembobinage complet."
        ),
    },
    {
        "id": "overload",
        "title": "Surcharge Moteur — Détection et protection",
        "keywords": ["surcharge", "overload", "courant", "nominal", "relais", "protection", "service factor"],
        "category": "fault",
        "content": (
            "La surcharge survient quand le moteur opère au-delà de sa puissance nominale.\n"
            "Signatures:\n"
            "• Courant > 1,1 × In (10% au-dessus du nominal)\n"
            "• Température stator élevée (> 80°C en classe B)\n"
            "• Facteur de puissance qui chute\n"
            "• Glissement augmenté\n"
            "Règles de protection:\n"
            "• 125% In pendant 1h: acceptable (service factor 1,15)\n"
            "• 150% In: relais de surcharge doit déclencher en < 2 min\n"
            "• 200% In: déclenchement < 30 sec\n"
            "Correction: Réduire la charge mécanique, vérifier le dimensionnement du moteur, "
            "inspecter l'équipement entraîné (pompe, ventilateur colmaté)."
        ),
    },
    {
        "id": "early_degradation",
        "title": "Dégradation Précoce — Détection anticipée",
        "keywords": ["dégradation précoce", "early degradation", "tendance", "hausse", "prévention", "anticipation"],
        "category": "fault",
        "content": (
            "La dégradation précoce est détectable avant que les seuils d'alarme soient atteints.\n"
            "Indicateurs:\n"
            "• Température ET vibrations en tendance haussière simultanée\n"
            "• Évolution lente mais continue des KPI sur plusieurs semaines\n"
            "• Anomalies Isolation Forest sur les données de processus\n"
            "Causes probables:\n"
            "• Usure initiale des roulements (Phase 1 — micro-fissures)\n"
            "• Déséquilibre rotor naissant (dépôt progressif)\n"
            "• Dégradation lubrification\n"
            "Action recommandée: inspection préventive dans les 30 jours, "
            "augmenter la fréquence de surveillance à toutes les 4h."
        ),
    },

    # ── Maintenance ──────────────────────────────────────────────────────
    {
        "id": "predictive_maintenance",
        "title": "Maintenance Prédictive — Méthodologie",
        "keywords": ["maintenance prédictive", "cbm", "rul", "remaining useful life", "planification", "plan"],
        "category": "maintenance",
        "content": (
            "La maintenance prédictive (CBM - Condition Based Maintenance) réduit les coûts de 25-30%.\n"
            "Niveaux d'intervention:\n"
            "• Niveau 1 (Opérateur): Surveillance visuelle, prise de mesures, reporting anomalies\n"
            "• Niveau 2 (Technicien): Analyse vibratoire, mesures électriques, diagnostic\n"
            "• Niveau 3 (Expert): Analyse spectrale FFT, tests d'isolation, rembobinage\n"
            "RUL (Remaining Useful Life):\n"
            "• Score Santé > 75%: RUL estimé > 6 mois\n"
            "• Score Santé 50-75%: RUL 1-6 mois, planifier maintenance\n"
            "• Score Santé < 50%: RUL < 1 mois, intervention urgente\n"
            "KPIs de maintenance: MTBF, MTTR, disponibilité, OEE."
        ),
    },
    {
        "id": "lubrication",
        "title": "Lubrification des Roulements — Bonnes pratiques",
        "keywords": ["lubrification", "graisse", "huile", "roulement", "intervalle", "viscosité"],
        "category": "maintenance",
        "content": (
            "80% de la durée de vie d'un roulement dépend de la lubrification.\n"
            "Intervalles recommandés:\n"
            "• Moteurs < 30 kW: tous les 6 mois (ou 2000h)\n"
            "• Moteurs 30-100 kW: tous les 3 mois (ou 1000h)\n"
            "• Moteurs > 100 kW: tous les mois (ou 500h)\n"
            "Quantité: 30% du volume du palier (sur-graissage = surchauffe)\n"
            "Viscosité: ISO VG 68-150 selon vitesse et charge\n"
            "Symptômes de sous-lubrification: température roulement en hausse + bruit métallique\n"
            "Symptômes de sur-lubrification: température élevée + débordement de graisse"
        ),
    },
]


def search(query: str, top_k: int = 3) -> list[dict]:
    """Keyword-based search. Returns top_k most relevant entries."""
    q_words = set(query.lower().split())
    scored  = []

    for entry in KNOWLEDGE_BASE:
        kw_set = {k.lower() for k in entry["keywords"]}
        # Keyword overlap score
        kw_score = len(q_words & kw_set)
        # Title word overlap
        title_words = set(entry["title"].lower().split())
        title_score = len(q_words & title_words) * 2
        # Content substring match
        content_score = sum(1 for w in q_words if w in entry["content"].lower() and len(w) > 3)

        total = kw_score + title_score + content_score
        if total > 0:
            scored.append((total, entry))

    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:top_k]]


def format_for_prompt(entries: list[dict]) -> str:
    if not entries:
        return ""
    lines = ["=== BASE DE CONNAISSANCES ORBIT AI ==="]
    for e in entries:
        lines.append(f"\n[{e['title']}]\n{e['content']}")
    lines.append("======================================")
    return "\n".join(lines)
